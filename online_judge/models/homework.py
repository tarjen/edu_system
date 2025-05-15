from online_judge import db
from datetime import datetime
from .questions import Question, QuestionType
import json

# 作业-题目关联表
class HomeworkQuestion(db.Model):
    __tablename__ = 'homework_question'
    
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 题目分值
    
    # 创建索引提高查询效率
    __table_args__ = (
        db.Index('idx_homework_question', 'homework_id', 'question_id'),
    )

class Homework(db.Model):
    """作业模型"""
    __tablename__ = 'homework'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    holder_id = db.Column(db.Integer, nullable=False)
    holder_name = db.Column(db.String(128), nullable=False)
    
    # 通过关联表关联题目
    questions = db.relationship('Problem', 
                              secondary='homework_question',
                              backref=db.backref('homeworks', lazy='dynamic'),
                              lazy='dynamic')
    
    def __init__(self, title, description, start_time, end_time, holder_id, holder_name):
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.holder_id = holder_id
        self.holder_name = holder_name

    def to_dict(self):
        # 基础信息
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'end_time': self.end_time.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'holder_name': self.holder_name,
        }
    
    @staticmethod
    def from_dict(data):
        homework = Homework(
            title=data['title'],
            description=data.get('description', ''),
            start_time=datetime.strptime(data['start_time'], '%a, %d %b %Y %H:%M:%S GMT'),
            end_time=datetime.strptime(data['end_time'], '%a, %d %b %Y %H:%M:%S GMT'),
            holder_name=data['holder_name'],
        )
        return homework
        
    def update_questions(self, question_scores):
        """更新作业题目和分值
        
        Args:
            question_scores: [{'question_id': int, 'score': float}, ...]
        Returns:
            (bool, str): (是否成功, 消息)
        """
        print(f"id: {self.id}, question_scores: {question_scores}")
        try:
            # 验证题目是否存在
            question_ids = [item['question_id'] for item in question_scores]
            existing_questions = Question.query.filter(Question.id.in_(question_ids)).all()
            if len(existing_questions) != len(question_ids):
                return False, "存在无效的题目ID"
            
            # 获取原有题目ID
            old_questions = HomeworkQuestion.query.filter_by(homework_id=self.id).all()
            old_question_ids = [q.question_id for q in old_questions]
            
            # 更新题目used_times
            questions_dict = {q.id: q for q in existing_questions}
            for qid in old_question_ids:
                if qid not in question_ids and qid in questions_dict:
                    questions_dict[qid].used_times -= 1
            for qid in question_ids:
                if qid not in old_question_ids:
                    questions_dict[qid].used_times += 1
            
            # 删除原有关联
            HomeworkQuestion.query.filter_by(homework_id=self.id).delete()
            
            # 添加新关联
            for item in question_scores:
                hw_question = HomeworkQuestion(
                    homework_id=self.id,
                    question_id=item['question_id'],
                    score=item['score']
                )
                db.session.add(hw_question)
            
            db.session.commit() 
            return True, "更新成功"
        except Exception as e:
            db.session.rollback()
            return False, f"更新失败: {str(e)}"
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True, "保存成功"
        except Exception as e:
            db.session.rollback()
            return False, f"保存失败: {str(e)}"

    def delete(self):
        try:
            # 先删除关联的题目记录
            HomeworkQuestion.query.filter_by(homework_id=self.id).delete()
            # 再删除作业本身
            db.session.delete(self)
            db.session.commit()
            return True, "删除成功"
        except Exception as e:
            db.session.rollback()
            return False, f"删除失败: {str(e)}"
    
class HomeworkStudent(db.Model):
    """学生作业答题记录"""
    __tablename__ = 'homework_student'
    
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), primary_key=True)
    student_id = db.Column(db.Integer, primary_key=True)
    answer = db.Column('answer', db.Text)  # JSON格式存储答案列表
    score = db.Column(db.Integer, default=0)  # 该学生得分
    submit_time = db.Column(db.DateTime)  # 提交时间
    
    # 关系
    homework = db.relationship('Homework')
    
    def get_answer(self):
        """获取答案列表"""
        return json.loads(self.answer) if self.answer else []
        
    def submit(self, answer_list):
        """提交答案并计算分数
        Args:
            answer_list: 学生答案列表，格式为[{"question_id": 题目ID, "answer": "答案内容"}, ...]
        Returns:
            (bool, str): (是否成功, 消息)
        """
        try:
            # 检查作业时间
            now = datetime.now()
            if now < self.homework.start_time or now > self.homework.end_time:
                return False, "不在作业时间范围内"
                
            # 验证答案格式
            if not isinstance(answer_list, list):
                return False, "答案格式错误"
            
            # 获取作业题目和分值信息
            homework_questions = HomeworkQuestion.query.filter_by(homework_id=self.homework_id).all()
            print(f"self.homework_id: {self.homework_id}")
            print(f"homework_questions: {homework_questions}")
            print(f"answer_list: {answer_list}")
            if len(answer_list) != len(homework_questions):
                return False, "答案数量与题目数量不匹配"
            
            # 创建题目ID到分值的映射
            question_scores = {hq.question_id: hq.score for hq in homework_questions}
            
            # 存储答案
            self.answer = json.dumps(answer_list)
            self.submit_time = now
            
            # 计算总分
            total_score = 0
            for ans in answer_list:
                if not isinstance(ans, dict) or "question_id" not in ans or "answer" not in ans:
                    return False, "答案格式错误，每个答案必须包含question_id和answer字段"
                
                question_id = ans["question_id"]
                student_ans = ans["answer"]
                
                # 获取题目信息
                question = Question.query.get(question_id)
                if not question:
                    continue
                
                # 根据题目类型进行答案比对
                is_correct = False
                if question.question_type == QuestionType.CHOICE:
                    # 选择题比对（不区分大小写）
                    is_correct = student_ans.upper() == question.answer.upper()
                elif question.question_type == QuestionType.FILL:
                    # 填空题比对（去除首尾空格后完全相同）
                    is_correct = student_ans.strip() == question.answer.strip()
                
                # 计分
                if is_correct:
                    total_score += question_scores.get(question_id, 0)
                    question.update_stats(True)
                else:
                    question.update_stats(False)
            
            self.score = total_score
            db.session.commit()
            return True, "提交成功"
            
        except Exception as e:
            db.session.rollback()
            return False, f"提交失败: {str(e)}"

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True, "保存成功"
        except Exception as e:
            db.session.rollback()
            return False, f"保存失败: {str(e)}"

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True, "删除成功"
        except Exception as e:
            db.session.rollback()
            return False, f"删除失败: {str(e)}"