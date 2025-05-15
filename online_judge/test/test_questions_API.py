import unittest,json
from datetime import datetime
from flask import Flask
from online_judge import db,app
from online_judge.models.questions import Question, QuestionType
from online_judge.models.homework import Homework, HomeworkStudent
from online_judge.models.problems import Tag

class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

class ChoiceFillHomeworkAPITestCase(unittest.TestCase):
    def setUp(self):
        # 创建全新的Flask应用实例（避免全局状态污染）
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # 创建应用上下文并激活
        self.app_context = app.app_context()
        self.app_context.push()
        
        # 初始化数据库结构
        db.drop_all()
        db.create_all()
        
        # 创建测试客户端
        self.client = app.test_client()
        
        # 注入测试数据
        self.setup_test_data()

    def tearDown(self):
        # 清理数据库
        db.session.remove()
        db.drop_all()
        
        # 释放应用上下文
        self.app_context.pop()

    def setup_test_data(self):
        # 创建测试用户
        self.users = [
            User(id=1, username='admin', power=2),
            User(id=2, username='creator', power=1),
            User(id=3, username='user', power=1)
        ]
        
        # 创建测试选择题
        choice_question = Question(
            title="测试选择题",
            content="1+1=?",
            user_id=1,
            user_name="admin",
            question_type=QuestionType.CHOICE.value,
            answer="A",
            options=["2", "3", "4", "5"],
            options_count=4,
            difficulty=1,
            is_public=True
        )
        
        # 创建测试填空题
        fill_question = Question(
            title="测试填空题",
            content="请填写Python之父的名字",
            user_id=1,
            user_name="admin",
            question_type=QuestionType.FILL.value,
            answer="Guido van Rossum",
            difficulty=2,
            is_public=True
        )
        
        db.session.add(choice_question)
        db.session.add(fill_question)
        db.session.commit()
        
        # 创建测试作业
        homework = Homework(
            title="测试作业",
            holder_id=2,
            holder_name="creator",
            start_time=datetime(2025, 1, 1, 8, 0, 0),
            end_time=datetime(2025, 1, 2, 8, 0, 0),
            description="这是一个测试作业"
        )
        
        # 添加题目到作业
        homework.update_questions([
            {"question_id": 1, "score": 50},
            {"question_id": 2, "score": 50}
        ])
        
        db.session.add(homework)
        
        # 创建学生作业记录
        homework_student = HomeworkStudent(
            homework_id=1,
            student_id=3
        )
        db.session.add(homework_student)
        db.session.commit()

        # 生成测试token
        self.tokens = {
            'admin': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxIiwic3ViIjoiMTEiLCJwb3dlciI6IjIiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiYWRtaW4ifQ.ZCCkJ0r0ghLvSEKViBY3MtOeBf_GgzJ3y7ZO9eTuvv8',
            'user': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoidXNlciJ9.NwUOdtcAs5KzOMtNiC8qZj4qad3OZ85f1_qqWH-GaDA',
            'creator': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiY3JlYXRvciJ9.mz4JKpGvW8MQGPHU20L3JiMTjbNpH6B26798NiCcNB8'
        }

    # 辅助方法
    def get_headers(self, token_key):
        return {'token': self.tokens[token_key]}
    
    # 测试用例分割线 --------------------------------------------------------

    def test_get_question_admin(self):
        """测试管理员获取题目详情"""
        response = self.client.get('/api/questions/get/1', headers=self.get_headers('admin'))
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], "测试选择题")
        self.assertTrue('answer' in data)  # 管理员可以看到答案
        self.assertEqual(data['options_count'], 4)
        
    def test_get_question_student(self):
        """测试学生获取公开题目详情"""
        response = self.client.get('/api/questions/get/1', headers=self.get_headers('user'))
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], "测试选择题")
        self.assertFalse('answer' in data)  # 学生看不到答案
        
    def test_get_nonexistent_question(self):
        """测试获取不存在的题目"""
        response = self.client.get('/api/questions/get/999', headers=self.get_headers('admin'))
        self.assertEqual(response.status_code, 404)
        
    def test_filter_questions_by_type(self):
        """测试按类型筛选题目"""
        data = {
            'type': 'choice'
        }
        response = self.client.post('/api/questions/filter', 
                                  headers=self.get_headers('admin'),
                                  json=data)
        questions = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['type'], 'choice')
        
    def test_filter_questions_by_difficulty(self):
        """测试按难度筛选题目"""
        data = {
            'min_difficulty': 1,
            'max_difficulty': 2
        }
        response = self.client.post('/api/questions/filter', 
                                  headers=self.get_headers('admin'),
                                  json=data)
        questions = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(questions), 2)  # 应该返回所有测试题目
        
    def test_create_choice_question(self):
        """测试创建选择题"""
        data = {
            'title': '新建选择题',
            'content': '2+2=?',
            'question_type': 'choice',
            'options': ['3', '4', '5', '6'],
            'options_count': 4,
            'answer': 'B',
            'difficulty': 2,
            'is_public': True,
            'tags': ['数学', '基础']
        }
        response = self.client.post('/api/questions/create', 
                                  headers=self.get_headers('creator'),
                                  json=data)
        
        self.assertEqual(response.status_code, 201)
        created = json.loads(response.data)['question']
        self.assertEqual(created['title'], '新建选择题')
        self.assertEqual(created['options_count'], 4)
        
    def test_create_fill_question(self):
        """测试创建填空题"""
        data = {
            'title': '新建填空题',
            'content': 'Python最新的大版本号是?',
            'question_type': 'fill',
            'answer': '3',
            'difficulty': 1,
            'is_public': True,
            'tags': ['Python', '基础']
        }
        response = self.client.post('/api/questions/create', 
                                  headers=self.get_headers('creator'),
                                  json=data)
        
        self.assertEqual(response.status_code, 201)
        created = json.loads(response.data)['question']
        self.assertEqual(created['title'], '新建填空题')
        
    def test_update_question(self):
        """测试更新题目"""
        data = {
            'title': '更新后的选择题',
            'content': '1+1=?（更新）',
            'difficulty': 3,
            'tags': ['数学', '更新']
        }
        response = self.client.post('/api/questions/update/1', 
                                 headers=self.get_headers('admin'),
                                 json=data)
        
        self.assertEqual(response.status_code, 200)
        updated = json.loads(response.data)['question']
        self.assertEqual(updated['title'], '更新后的选择题')
        self.assertEqual(updated['difficulty'], 3)
        
    def test_update_unauthorized(self):
        """测试未授权更新题目"""
        data = {
            'title': '未授权更新'
        }
        response = self.client.post('/api/questions/update/1', 
                                 headers=self.get_headers('user'),
                                 json=data)
        
        self.assertEqual(response.status_code, 403)
        
    def test_delete_question(self):
        """测试删除题目"""
        # 先创建一个新题目
        data = {
            'title': '待删除题目',
            'content': '这个题目将被删除',
            'question_type': 'fill',
            'answer': '测试',
            'difficulty': 1
        }
        create_response = self.client.post('/api/questions/create', 
                                         headers=self.get_headers('creator'),
                                         json=data)
        question_id = json.loads(create_response.data)['question']['id']
        
        # 删除题目
        response = self.client.post(f'/api/questions/delete/{question_id}', 
                                    headers=self.get_headers('creator'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['success'])
        
        # 确认题目已被删除
        get_response = self.client.get(f'/api/questions/get/{question_id}', 
                                     headers=self.get_headers('admin'))
        self.assertEqual(get_response.status_code, 404)
        
    def test_invalid_question_type(self):
        """测试无效的题目类型"""
        data = {
            'title': '无效题目类型',
            'content': '测试内容',
            'question_type': 'invalid_type',
            'answer': 'A'
        }
        response = self.client.post('/api/questions/create', 
                                  headers=self.get_headers('creator'),
                                  json=data)
        
        self.assertEqual(response.status_code, 400)
        
    def test_filter_questions_invalid_params(self):
        """测试无效的筛选参数"""
        data = {
            'min_difficulty': 1  # 缺少max_difficulty
        }
        response = self.client.post('/api/questions/filter', 
                                  headers=self.get_headers('admin'),
                                  json=data)
        
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main() 