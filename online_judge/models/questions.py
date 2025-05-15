from online_judge import db
from datetime import datetime
import json
from enum import Enum

class QuestionType(Enum):
    CHOICE = 'choice'    # 选择题
    FILL = 'fill'       # 填空题

class Question(db.Model):
    """选择题和填空题统一模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), index=True)
    content = db.Column(db.Text, nullable=False)  # 题面
    
    # 从Problem类继承的字段
    user_id = db.Column(db.Integer, index=True)
    user_name = db.Column(db.String(80))
    difficulty = db.Column(db.Integer, default=1)
    accept_num = db.Column(db.Integer, default=0)
    submit_num = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=False)
    used_times = db.Column(db.Integer, default=0)
    
    # 题目类型
    question_type = db.Column(db.String(20), nullable=False)
    
    # 选择题专用字段
    options_count = db.Column(db.Integer)  # 选项个数，如4表示A,B,C,D
    options = db.Column(db.Text)  # 选项内容，JSON格式["选项A", "选项B", "选项C", "选项D"]
    
    # 答案字段
    answer = db.Column(db.String(100), nullable=False)  # 选择题形如"AB"，填空题直接存答案
    explanation = db.Column(db.Text)  # 解析
    
    # 标签关联
    tags = db.relationship('Tag', secondary='question_tag', backref='questions')
    
    def __init__(self, title, content, user_id, user_name, question_type, answer,used_times=0,submit_num=0,accept_num=0, 
                 options=None, options_count=None, explanation=None, difficulty=1, is_public=False):
        self.title = title
        self.content = content
        self.user_id = user_id
        self.user_name = user_name
        self.used_times = used_times
        self.submit_num = submit_num
        self.accept_num = accept_num
        self.question_type = question_type
        self.answer = answer
        
        if question_type == QuestionType.CHOICE.value:
            if options is None or options_count is None:
                raise ValueError("选择题必须提供选项和选项个数")
            self.options_count = options_count  # 先设置options_count
            self.set_options(options)  # 再设置options
            
        self.explanation = explanation
        self.difficulty = difficulty
        self.is_public = is_public
        
    def set_options(self, options_list):
        """设置选择题选项"""
        if self.question_type == QuestionType.CHOICE.value:
            if len(options_list) != self.options_count:
                raise ValueError(f"选项个数必须为{self.options_count}")
            self.options = json.dumps(options_list)
    
    def get_options(self):
        """获取选择题选项"""
        if self.options:
            return json.loads(self.options)
        return []
    
    def update_stats(self, is_correct):
        """更新统计信息"""
        self.submit_num += 1
        if is_correct:
            self.accept_num += 1
    
    @property
    def accuracy_rate(self):
        """计算正确率"""
        if self.submit_num == 0:
            return 0
        return self.accept_num / self.submit_num * 100

    def update_problem(self, title=None, content=None, options=None, answer=None, explanation=None, difficulty=None, is_public=None):
        """更新题目信息
        Args:
            title: 题目标题
            content: 题目内容
            options: 选择题选项列表
            answer: 答案
            explanation: 解析
            difficulty: 难度
            is_public: 是否公开
        Returns:
            (bool, str): (是否成功, 消息)
        """
        try:
            if title is not None:
                self.title = title
            if content is not None:
                self.content = content
            if options is not None and self.question_type == QuestionType.CHOICE.value:
                self.set_options(options)
            if answer is not None:
                self.answer = answer
            if explanation is not None:
                self.explanation = explanation
            if difficulty is not None:
                self.difficulty = difficulty
            if is_public is not None:
                self.is_public = is_public
                
            return True, "更新成功"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, "更新失败"

# 题目-标签关联表
question_tag = db.Table('question_tag',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
) 