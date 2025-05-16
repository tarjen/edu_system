import unittest
from datetime import datetime, timedelta
from flask import json
from online_judge import app, db
from online_judge.models.questions import Question, QuestionType
from online_judge.models.problems import Tag
import random

class HomeworkGenerationTestCase(unittest.TestCase):
    # 配置参数
    TOTAL_CHOICE_QUESTIONS = 300  # 选择题总数
    TOTAL_FILL_QUESTIONS = 300    # 填空题总数
    MIN_TAGS_PER_QUESTION = 3      # 每题最少标签数
    MAX_TAGS_PER_QUESTION = 5      # 每题最多标签数
    BATCH_SIZE = 100               # 每次提交的题目数量
    
    def setUp(self):
        """测试前的准备工作"""
        print("\n=== 开始测试 ===")
        self.app = app.test_client()
        
        # 创建应用上下文并激活
        self.app_context = app.app_context()
        self.app_context.push()
        
        # 初始化数据库
        db.drop_all()
        db.create_all()
        
        # 生成测试数据
        print("\n=== 生成测试数据 ===")
        print(f"计划生成选择题: {self.TOTAL_CHOICE_QUESTIONS}道")
        print(f"计划生成填空题: {self.TOTAL_FILL_QUESTIONS}道")
        self.setup_test_data()
        
        # 模拟教师用户Token
        self.teacher_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiY3JlYXRvciJ9.mz4JKpGvW8MQGPHU20L3JiMTjbNpH6B26798NiCcNB8"

    def tearDown(self):
        """测试清理工作"""
        print("\n=== 清理测试环境 ===")
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def setup_test_data(self):
        """生成测试数据"""
        # 创建标签
        print("\n创建标签...")
        tags = [
            # 数据结构
            "数组", "字符串", "链表", "栈", "队列", "树", "图", "堆", "哈希表",
            # 算法思想
            "动态规划", "贪心", "回溯", "分治", "递归", "二分查找", "排序", "双指针",
            # 具体算法
            "深度优先搜索", "广度优先搜索", "并查集", "拓扑排序", "最短路径",
            # 数学
            "数学", "概率统计", "线性代数", "微积分", "组合数学",
            # 计算机基础
            "操作系统", "计算机网络", "数据库", "编译原理", "计算机组成"
        ]
        for tag_name in tags:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        db.session.commit()
        print(f"已创建{len(tags)}个标签")

        # 生成选择题
        print("\n生成选择题...")
        for i in range(1, self.TOTAL_CHOICE_QUESTIONS + 1):
            # 随机选择3-5个标签
            question_tags = random.sample(tags, k=random.randint(self.MIN_TAGS_PER_QUESTION, self.MAX_TAGS_PER_QUESTION))
            # 随机生成难度
            difficulty = random.randint(1, 5)
            
            # 生成随机答案和选项
            answer = random.choice(['A', 'B', 'C', 'D'])
            options = [
                f"选项A - 这是第{i}题的A选项",
                f"选项B - 这是第{i}题的B选项",
                f"选项C - 这是第{i}题的C选项",
                f"选项D - 这是第{i}题的D选项"
            ]
            
            question = Question(
                title=f"选择题 {i}",
                content=f"这是第{i}道选择题的内容，请仔细阅读并选择正确答案。",
                user_id=1,
                user_name="admin",
                question_type=QuestionType.CHOICE.value,
                answer=answer,
                options=options,
                options_count=4,
                difficulty=difficulty,
                is_public=True
            )
            # 添加标签
            for tag_name in question_tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                question.tags.append(tag)
            
            db.session.add(question)
            if i % self.BATCH_SIZE == 0:  # 每BATCH_SIZE题提交一次
                print(f"已生成{i}道选择题")
                db.session.commit()
        
        # 生成填空题
        print("\n生成填空题...")
        for i in range(1, self.TOTAL_FILL_QUESTIONS + 1):
            # 随机选择3-5个标签
            question_tags = random.sample(tags, k=random.randint(self.MIN_TAGS_PER_QUESTION, self.MAX_TAGS_PER_QUESTION))
            # 随机生成难度
            difficulty = random.randint(1, 5)
            
            question = Question(
                title=f"填空题 {i}",
                content=f"这是第{i}道填空题的内容，请根据题目要求填写正确答案。",
                user_id=1,
                user_name="admin",
                question_type=QuestionType.FILL.value,
                answer=f"这是第{i}道填空题的标准答案",
                difficulty=difficulty,
                is_public=True
            )
            # 添加标签
            for tag_name in question_tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                question.tags.append(tag)
            
            db.session.add(question)
            if i % self.BATCH_SIZE == 0:  # 每BATCH_SIZE题提交一次
                print(f"已生成{i}道填空题")
                db.session.commit()
        
        print("\n测试数据生成完成！")
        print(f"- 选择题：{self.TOTAL_CHOICE_QUESTIONS}道")
        print(f"- 填空题：{self.TOTAL_FILL_QUESTIONS}道")
        print(f"- 标签：{len(tags)}个")

    def test_generate_homework_success(self):
        """测试成功生成作业"""
        print("\n测试成功生成作业的情况")
        data = {
            "title": "测试作业",
            "description": "这是一个测试作业",
            "start_time": datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            "end_time": (datetime.now() + timedelta(days=7)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            "total_score": 100,
            "questions_config": {
                "choice_count": 30,
                "fill_count": 30
            },
            "difficulty_range": {
                "min": 1.3,
                "max": 5
            },
            "tags": ["数组", "字符串", "动态规划", "数学"]  # 增加标签数量
        }
        
        print("\n发送请求数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        response = self.app.post(
            '/api/homework/generate',
            headers={"token": self.teacher_token},
            json=data
        )
        
        print("\n收到响应:")
        print(f"状态码: {response.status_code}")
        print(json.dumps(json.loads(response.data), indent=2, ensure_ascii=False))
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result["success"])
        
        # 验证生成的作业
        homework = result["homework"]
        self.assertEqual(homework["title"], data["title"])
        self.assertEqual(homework["description"], data["description"])
        self.assertEqual(len(homework["questions"]), 60)  # 30选择题 + 30填空题
        
        # 输出题目分析
        print("\n=== 生成的试卷分析 ===")
        choice_questions = [q for q in homework["questions"] if q["type"] == QuestionType.CHOICE.value]
        fill_questions = [q for q in homework["questions"] if q["type"] == QuestionType.FILL.value]
        
        print(f"\n1. 题型分布:")
        print(f"- 选择题: {len(choice_questions)}题")
        print(f"- 填空题: {len(fill_questions)}题")
        
        print(f"\n2. 题目难度分布:")
        difficulties = [q["difficulty"] for q in homework["questions"]]
        avg_difficulty = sum(difficulties) / len(difficulties)
        print(f"- 平均难度: {avg_difficulty:.2f}")
        print(f"- 难度分布:")
        for diff in range(1, 6):
            count = sum(1 for d in difficulties if d == diff)
            print(f"  难度{diff}: {count}题 ({count/len(difficulties)*100:.1f}%)")
        
        print(f"\n3. 分数分布:")
        total_score = sum(q["score"] for q in homework["questions"])
        print(f"- 总分: {total_score}")
        print(f"- 每题分数: {homework['questions'][0]['score']}")
        
        print(f"\n4. 标签分布:")
        all_tags = []
        for q in homework["questions"]:
            question = Question.query.get(q["id"])
            all_tags.extend([tag.name for tag in question.tags])
        unique_tags = set(all_tags)
        print(f"- 覆盖标签数: {len(unique_tags)}")
        for tag in sorted(unique_tags):
            count = all_tags.count(tag)
            print(f"  {tag}: {count}题 ({count/len(homework['questions'])*100:.1f}%)")

if __name__ == '__main__':
    unittest.main()