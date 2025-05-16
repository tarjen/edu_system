from datetime import datetime
from flask import request, jsonify
from online_judge import app, jwt_required, get_jwt
from online_judge.models.questions import Question, QuestionType
from online_judge.models.homework import Homework, HomeworkQuestion
from online_judge.models.homework import HomeworkStudent
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Optional
import random
from sqlalchemy import and_, or_
from online_judge.models.problems import Tag

class GeneticAlgorithm:
    def __init__(self, 
                 total_score: int,
                 questions_config: Dict[str, int],
                 difficulty_range: Dict[str, int],
                 tags: Optional[List[str]] = None,
                 population_size: int = 50,
                 max_generations: int = 100,
                 crossover_rate: float = 0.8,
                 mutation_rate: float = 0.1,
                 f1: float = 0.5,  # 知识点分布权重
                 f2: float = 0.5   # 难度匹配权重
                ):
        self.total_score = total_score
        self.choice_count = questions_config['choice_count']
        self.fill_count = questions_config['fill_count']
        self.difficulty_range = difficulty_range
        self.tags = tags
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.f1 = f1
        self.f2 = f2
        
        # 期望难度取难度范围的中间值
        self.expected_difficulty = (difficulty_range['min'] + difficulty_range['max']) / 2
        
        # 从数据库获取符合条件的题目
        self.choice_questions = self._get_questions(QuestionType.CHOICE.value)
        self.fill_questions = self._get_questions(QuestionType.FILL.value)
        if len(self.choice_questions) < self.choice_count or len(self.fill_questions) < self.fill_count:
            raise ValueError("题库中符合条件的题目数量不足")
            
        # 计算每道题的分数
        total_questions = self.choice_count + self.fill_count
        self.score_per_question = total_score / total_questions
        
    def _get_questions(self, question_type: str) -> List[Dict]:
        """从数据库获取符合条件的题目"""
        # 基本过滤条件
        filters = [
            Question.question_type == question_type,
            Question.difficulty >= self.difficulty_range['min'],
            Question.difficulty <= self.difficulty_range['max']
        ]
        
        # 获取题目
        base_query = Question.query.filter(and_(*filters))
        
        # 如果指定了标签，进行标签过滤
        if self.tags:
            # 对每个标签分别查询，然后取并集
            all_questions = set()
            for tag_name in self.tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    # 复制基础查询
                    tag_query = base_query.filter(Question.tags.contains(tag))
                    questions = tag_query.all()
                    # 将该标签下的题目加入集合
                    all_questions.update(questions)
            
            # 转换为列表
            questions = list(all_questions)
        else:
            # 如果没有标签要求，直接获取所有符合条件的题目
            questions = base_query.all()
        
        print(f"标签 {self.tags} 下找到 {len(questions)} 道 {question_type} 类型的题目")
        
        return [{
            'id': q.id,
            'title': q.title,
            'type': q.question_type,
            'difficulty': q.difficulty,
            'tags': [tag.name for tag in q.tags]
        } for q in questions]
        
    def _init_population(self) -> List[List[int]]:
        """初始化种群"""
        population = []
        for _ in range(self.population_size):
            # 随机选择题目ID组成染色体
            choice_ids = random.sample([q['id'] for q in self.choice_questions], self.choice_count)
            fill_ids = random.sample([q['id'] for q in self.fill_questions], self.fill_count)
            chromosome = choice_ids + fill_ids
            population.append(chromosome)
        return population
        
    def _calculate_fitness(self, chromosome: List[int]) -> float:
        """计算适应度"""
        # 获取选择的题目
        selected_questions = []
        for qid in chromosome:
            # 在choice_questions和fill_questions中查找题目
            question = next((q for q in self.choice_questions if q['id'] == qid), None)
            if not question:
                question = next((q for q in self.fill_questions if q['id'] == qid), None)
            if question:
                selected_questions.append(question)
                
        # 计算实际难度
        total_difficulty = sum(q['difficulty'] * self.score_per_question for q in selected_questions)
        actual_difficulty = total_difficulty / self.total_score
        
        # 计算知识点覆盖率
        expected_tags = set(self.tags) if self.tags else set()
        actual_tags = set()
        for q in selected_questions:
            actual_tags.update(q.get('tags', []))
        
        coverage_rate = len(actual_tags & expected_tags) / len(expected_tags) if expected_tags else 1.0
        
        # 计算适应度
        return 1 - (1 - coverage_rate) * self.f1 - abs(self.expected_difficulty - actual_difficulty) * self.f2
        
    def _select_parent(self, population: List[List[int]], fitnesses: List[float]) -> List[int]:
        """轮盘赌选择"""
        total_fitness = sum(fitnesses)
        if total_fitness == 0:
            return random.choice(population)
            
        r = random.uniform(0, total_fitness)
        current_sum = 0
        
        for chromosome, fitness in zip(population, fitnesses):
            current_sum += fitness
            if current_sum > r:
                return chromosome
                
        return population[-1]
        
    def _crossover(self, parent1: List[int], parent2: List[int]) -> tuple[List[int], List[int]]:
        """分段单点交叉"""
        if random.random() > self.crossover_rate:
            return parent1, parent2
            
        # 分别对选择题部分和填空题部分进行交叉
        cross_point1 = random.randint(0, self.choice_count - 1)
        cross_point2 = random.randint(self.choice_count, len(parent1) - 1)
        
        child1 = parent1[:cross_point1] + parent2[cross_point1:self.choice_count] + \
                parent1[self.choice_count:cross_point2] + parent2[cross_point2:]
                
        child2 = parent2[:cross_point1] + parent1[cross_point1:self.choice_count] + \
                parent2[self.choice_count:cross_point2] + parent1[cross_point2:]
                
        # 处理重复题目
        self._fix_duplicate(child1)
        self._fix_duplicate(child2)
        
        return child1, child2
        
    def _fix_duplicate(self, chromosome: List[int]):
        """处理重复题目"""
        choice_part = chromosome[:self.choice_count]
        fill_part = chromosome[self.choice_count:]
        
        # 修复选择题部分
        used = set()
        for i, qid in enumerate(choice_part):
            if qid in used:
                unused = set(q['id'] for q in self.choice_questions) - used
                if unused:
                    chromosome[i] = random.choice(list(unused))
            used.add(qid)
            
        # 修复填空题部分
        used = set()
        for i, qid in enumerate(fill_part, start=self.choice_count):
            if qid in used:
                unused = set(q['id'] for q in self.fill_questions) - used
                if unused:
                    chromosome[i] = random.choice(list(unused))
            used.add(qid)
            
    def _mutate(self, chromosome: List[int]):
        """局部变异"""
        if random.random() > self.mutation_rate:
            return
            
        # 随机选择一个位置进行变异
        pos = random.randint(0, len(chromosome) - 1)
        
        # 根据位置确定是选择题还是填空题
        if pos < self.choice_count:
            # 变异选择题
            available = [q['id'] for q in self.choice_questions if q['id'] not in chromosome[:self.choice_count]]
            if available:
                chromosome[pos] = random.choice(available)
        else:
            # 变异填空题
            available = [q['id'] for q in self.fill_questions if q['id'] not in chromosome[self.choice_count:]]
            if available:
                chromosome[pos] = random.choice(available)
                
    def evolve(self) -> List[Dict]:
        """进化过程"""
        # 初始化种群
        population = self._init_population()
        best_fitness = 0
        best_chromosome = None
        
        # 进化迭代
        for _ in range(self.max_generations):
            # 计算适应度
            fitnesses = [self._calculate_fitness(chrom) for chrom in population]
            
            # 更新最优解
            max_fitness = max(fitnesses)
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_chromosome = population[fitnesses.index(max_fitness)]
                
            # 如果找到了足够好的解，提前结束
            if best_fitness > 0.95:
                break
                
            # 生成新种群
            new_population = []
            while len(new_population) < self.population_size:
                # 选择父代
                parent1 = self._select_parent(population, fitnesses)
                parent2 = self._select_parent(population, fitnesses)
                
                # 交叉
                child1, child2 = self._crossover(parent1, parent2)
                
                # 变异
                self._mutate(child1)
                self._mutate(child2)
                
                new_population.extend([child1, child2])
                
            # 更新种群
            population = new_population[:self.population_size]
            
        # 返回最优解对应的题目列表
        if best_chromosome is None:
            raise ValueError("未能找到合适的题目组合")
            
        result = []
        for qid in best_chromosome:
            question = next((q for q in self.choice_questions if q['id'] == qid), None)
            if not question:
                question = next((q for q in self.fill_questions if q['id'] == qid), None)
            
            if question:
                result.append({
                    "id": question['id'],
                    "title": question['title'],
                    "type": question['type'],
                    "difficulty": question['difficulty'],
                    "score": self.score_per_question
                })
                
        return result

def gen_homework(
    total_score: int,
    questions_config: Dict[str, int],
    difficulty_range: Dict[str, int],
    tags: Optional[List[str]] = None
) -> List[Dict]:
    """生成作业题目集合的具体实现函数
    
    Args:
        total_score (int): 作业总分
        questions_config (Dict[str, int]): 题目配置，包含选择题和填空题的数量
            {"choice_count": int, "fill_count": int}
        difficulty_range (Dict[str, int]): 难度范围
            {"min": int, "max": int}
        tags (List[str], optional): 题目标签列表. 默认为None
        
    Returns:
        List[Dict]: 生成的题目列表，每个题目包含：
            [{
                "id": int,
                "title": str,
                "type": str,
                "difficulty": int,
                "score": int
            }]
            
    Raises:
        ValueError: 当参数验证失败时
        SQLAlchemyError: 当数据库操作失败时
    """
    # 创建遗传算法实例
    ga = GeneticAlgorithm(
        total_score=total_score,
        questions_config=questions_config,
        difficulty_range=difficulty_range,
        tags=tags
    )
    
    # 执行进化算法
    return ga.evolve()

@app.route('/api/homework/generate', methods=['POST'])
@jwt_required()
def generate_homework():
    """作业生成接口，根据要求自动生成作业题目集合。
    
    从题库中选择符合要求的题目组合生成作业。需要教师权限。
    """
    try:
        current_user = User(get_jwt())
        
        # 检查权限（只有教师和管理员可以生成作业）
        if current_user.power < 1:
            return jsonify({"error": "没有权限生成作业"}), 403
            
        data = request.get_json()
        print(f"test data: {data}")
        # 验证必填字段
        required_fields = ['title', 'start_time', 'end_time', 'questions_config', 'difficulty_range']
        if missing := [f for f in required_fields if f not in data]:
            return jsonify({"error": f"缺少必填字段: {missing}"}), 400
            
        # 验证题目配置
        questions_config = data['questions_config']
        if not isinstance(questions_config, dict) or 'choice_count' not in questions_config or 'fill_count' not in questions_config:
            return jsonify({"error": "题目配置必须包含choice_count和fill_count"}), 400
            
        if questions_config['choice_count'] < 0 or questions_config['fill_count'] < 0:
            return jsonify({"error": "题目数量不能为负数"}), 400
            
        if questions_config['choice_count'] + questions_config['fill_count'] == 0:
            return jsonify({"error": "至少需要一道题目"}), 400
            
        # 验证难度范围
        diff_range = data['difficulty_range']
        if not (isinstance(diff_range, dict) and 
                'min' in diff_range and 'max' in diff_range and
                1 <= diff_range['min'] <= diff_range['max'] <= 5):
            return jsonify({"error": "难度范围必须在1-5之间"}), 400
            
        try:
            # 调用作业生成函数生成题目列表
            questions = gen_homework(
                total_score=data.get('total_score', 100),
                questions_config=questions_config,
                difficulty_range=diff_range,
                tags=data.get('tags')
            )
        except Exception as e:
            print(f"生成题目失败: {str(e)}")
            return jsonify({"error": f"生成题目失败: {str(e)}"}), 500
            
        try:
            # 创建作业
            homework = Homework(
                title=data['title'],
                description=data.get('description', ''),
                start_time=datetime.strptime(data['start_time'], '%a, %d %b %Y %H:%M:%S GMT'),
                end_time=datetime.strptime(data['end_time'], '%a, %d %b %Y %H:%M:%S GMT'),
                holder_id=current_user.id,
                holder_name=current_user.name
            )
            
            # 保存作业
            success, message = homework.save()
            if not success:
                print(f"保存作业失败: {message}")
                return jsonify({"error": f"保存作业失败: {message}"}), 500
                
            # 添加题目关联
            question_scores = []
            for q in questions:
                question_scores.append({
                    'question_id': q['id'],
                    'score': q['score']
                })
                
            # 更新作业题目
            success, message = homework.update_questions(question_scores)
            if not success:
                print(f"更新作业题目失败: {message}")
                return jsonify({"error": f"更新作业题目失败: {message}"}), 500
                
            # 如果指定了学生，创建学生作业记录
            if 'student_ids' in data and data['student_ids']:
                for student_id in data['student_ids']:
                    homework_student = HomeworkStudent(
                        homework_id=homework.id,
                        student_id=student_id
                    )
                    success, message = homework_student.save()
                    if not success:
                        print(f"创建学生作业记录失败: {message}")
                        return jsonify({"error": f"创建学生作业记录失败: {message}"}), 500
            
            # 构建返回数据
            homework_dict = homework.to_dict()
            homework_dict['questions'] = questions
            homework_dict['total_score'] = data.get('total_score', 100)
            homework_dict['student_count'] = len(data.get('student_ids', []))
            
            return jsonify({
                "success": True,
                "homework": homework_dict
            })
            
        except Exception as e:
            print(f"创建作业失败: {str(e)}")
            return jsonify({"error": f"创建作业失败: {str(e)}"}), 500
            
    except ValueError as e:
        print(f"参数验证失败: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError as e:
        print(f"数据库操作失败: {str(e)}")
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return jsonify({"error": f"未知错误: {str(e)}"}), 500