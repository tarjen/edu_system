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
        app.config['JSON_AS_ASCII'] = False  # 设置JSON响应支持中文
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
            User(id=2, username='user', power=1),
            User(id=3, username='creator', power=1)
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
            holder_id=3,
            holder_name="creator",
            start_time=datetime(2025, 1, 1, 8, 0, 0),
            end_time=datetime(2027, 12, 31, 8, 0, 0),
            description="这是一个测试作业"
        )
        db.session.add(homework)
        db.session.commit()
        # 添加题目到作业
        homework.update_questions([
            {"question_id": 1, "score": 50},
            {"question_id": 2, "score": 50}
        ])
        
        db.session.add(homework)
        
        # 创建学生作业记录
        homework_student = HomeworkStudent(
            homework_id=1,
            student_id=2
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

    def test_get_homework_admin(self):
        """测试管理员获取作业详情"""
        response = self.client.get('/api/homework/show/1', headers=self.get_headers('admin'))
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], "测试作业")
        self.assertTrue('questions' in data)  # 管理员可以看到题目
        self.assertTrue('students' in data)   # 管理员可以看到学生列表
        
    def test_get_homework_creator(self):
        """测试创建者获取作业详情"""
        response = self.client.get('/api/homework/show/1', headers=self.get_headers('creator'))
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], "测试作业")
        self.assertTrue('questions' in data)  # 创建者可以看到题目
        self.assertTrue('students' in data)   # 创建者可以看到学生列表
        
    def test_get_homework_student(self):
        """测试学生获取作业详情"""
        response = self.client.get('/api/homework/show/1', headers=self.get_headers('user'))
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], "测试作业")
        self.assertTrue('questions' in data)       # 学生可以看到题目
        self.assertFalse('students' in data)      # 学生看不到其他学生
        self.assertTrue('student_record' in data)  # 学生可以看到自己的记录
        
    def test_create_homework(self):
        """测试创建作业"""
        data = {
            'title': '新建作业',
            'start_time': 'Wed, 26 Feb 2025 08:00:00 GMT',
            'end_time': 'Thu, 27 Feb 2025 08:00:00 GMT',
            'description': '这是一个新建的作业',
            'question_list': [
                {'question_id': 1, 'score': 60},
                {'question_id': 2, 'score': 40}
            ],
            'student_ids': [3]
        }
        response = self.client.post('/api/homework/create', 
                                  headers=self.get_headers('creator'),
                                  json=data)
        
        self.assertEqual(response.status_code, 201)
        created = json.loads(response.data)['homework']
        self.assertEqual(created['title'], '新建作业')
        
    def test_update_homework(self):
        """测试更新作业"""
        data = {
            'title': '更新后的作业',
            'description': '这是更新后的作业描述',
            'question_list': [
                {'question_id': 1, 'score': 100}
            ]
        }
        response = self.client.post('/api/homework/update/1', 
                                 headers=self.get_headers('creator'),
                                 json=data)
        
        self.assertEqual(response.status_code, 200)
        updated = json.loads(response.data)['homework']
        self.assertEqual(updated['title'], '更新后的作业')
        
    def test_delete_homework(self):
        """测试删除作业"""
        # 先创建一个新作业
        data = {
            'title': '待删除作业',
            'start_time': 'Wed, 26 Feb 2025 08:00:00 GMT',
            'end_time': 'Thu, 27 Feb 2025 08:00:00 GMT',
            'description': '这个作业将被删除'
        }
        create_response = self.client.post('/api/homework/create', 
                                         headers=self.get_headers('creator'),
                                         json=data)
        homework_id = json.loads(create_response.data)['homework']['id']
        
        # 删除作业
        response = self.client.post(f'/api/homework/delete/{homework_id}', 
                                  headers=self.get_headers('creator'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['success'])
        
        # 确认作业已被删除
        get_response = self.client.get(f'/api/homework/show/{homework_id}', 
                                     headers=self.get_headers('admin'))
        self.assertEqual(get_response.status_code, 404)
        
    def test_submit_homework(self):
        """测试提交作业"""
        data = {
            'answer_list': [
                {'question_id': 1, 'answer': 'A'},
                {'question_id': 2, 'answer': 'Python'}
            ]
        }
        response = self.client.post('/api/homework/submit/1', 
                                  headers=self.get_headers('user'),
                                  json=data)
        
        print(f"response.data: {response.data}")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertTrue('score' in result)
        self.assertTrue('submit_time' in result)
        
    def test_submit_homework_twice(self):
        """测试重复提交作业"""
        # 第一次提交
        data = {
            'answer_list': [
                {'question_id': 1, 'answer': 'A'},
                {'question_id': 2, 'answer': 'Python'}
            ]
        }
        self.client.post('/api/homework/submit/1', 
                        headers=self.get_headers('user'),
                        json=data)
        
        # 第二次提交
        response = self.client.post('/api/homework/submit/1', 
                                  headers=self.get_headers('user'),
                                  json=data)
        
        self.assertEqual(response.status_code, 400)  # 应该返回错误
        
    def test_filter_homeworks(self):
        """测试筛选作业"""
        # 按标题筛选
        data = {
            'title': '测试'
        }
        response = self.client.post('/api/homework/filter', 
                                  headers=self.get_headers('admin'),
                                  json=data)
        homeworks = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(homeworks) > 0)
        self.assertTrue(all('测试' in h['title'] for h in homeworks))
        
        # 按创建者筛选
        data = {
            'holder_name': 'creator'
        }
        response = self.client.post('/api/homework/filter', 
                                  headers=self.get_headers('admin'),
                                  json=data)
        homeworks = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(homeworks) > 0)
        self.assertTrue(all(h['holder_name'] == 'creator' for h in homeworks))

if __name__ == '__main__':
    unittest.main() 