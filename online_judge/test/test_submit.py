import unittest,json,os
from datetime import datetime
from flask import Flask
from online_judge import db,app
from online_judge.models import Contest, Problem, Submission, Tag, ContestUser
from dotenv import load_dotenv

class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

class SubmitAPITestCase(unittest.TestCase):
    def setUp(self):
        # 创建全新的Flask应用实例（避免全局状态污染）

        load_dotenv('.flaskenv')  # 显式指定加载.flaskenv
        load_dotenv('.env')       # 可选的额外加载

        app.config['TESTING'] = True
        self.client = app.test_client()
        # 初始化数据库扩展
        
        # 创建应用上下文并激活
        self.app_context = app.app_context()
        self.app_context.push()
        
        # 初始化数据库结构
        db.drop_all()
        db.create_all()
        
        # 创建测试客户端（必须在上下文激活后创建）
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

        self.testcodepath = "/home/shuacm/Desktop/edu_system/online_judge/test/code_for_test"
        self.users = [
            User(id=1, username='admin', power=2),
            User(id=2, username='user', power=1),
            User(id=3, username='creator', power=1)
        ]
        
        contests = [
            Contest(
                title="Admin's Contest",
                start_time=datetime(2025, 1, 1, 8, 0, 0),  # 补充必填字段
                end_time=datetime(2025, 1, 2, 8, 0, 0),
                holder_id=1,
                holder_name="admin"  # 对应User.username
            ),
            Contest(
                title="User's Contest",
                start_time=datetime(2025, 2, 1, 9, 0, 0),
                end_time=datetime(2025, 2, 2, 9, 0, 0),
                holder_id=3,
                holder_name="creator"
            )
        ]

        db.session.bulk_save_objects(contests)
        db.session.commit()

        # 创建测试题目（完全符合Problem构造函数）
        problems = [
            Problem(
                title="Problem 1",
                user_id=1,
                user_name="admin",  # 对应User.username
                difficulty=1,
                is_public=True,
                time_limit=1000,    # 默认值
                memory_limit=256    # 默认值
            ),
            Problem(
                title="Problem 2",
                user_id=1,
                user_name="admin",
                difficulty=2,
                is_public=False,
                time_limit=2000,
                memory_limit=512
            )
        ]
        db.session.bulk_save_objects(problems)
        db.session.commit()
        # 创建测试提交记录（完全符合Submission构造函数）

        # 创建ContestUser测试数据
        contest_users = [
            # 用户1001参加两个比赛
            ContestUser(
                contest_id=1,
                user_id=1,
            ),
            ContestUser(
                contest_id=1,
                user_id=2,
            ),
        ]
        db.session.bulk_save_objects(contest_users)
        db.session.commit()

        submissions = [
            Submission(
                code="print('Hello')",
                language="python",
                user_id=2,
                problem_id=1,
                contest_id=1,
                submit_time=datetime(2025, 1, 1, 10, 0, 0),  # 在比赛时间内
            ),
            Submission(
                code="Code cpp 2",
                language="cpp",
                user_id=2,
                problem_id=2,
                contest_id=1,
                submit_time=datetime(2025, 1, 1, 11, 0, 0),
            )
        ]

        # 创建标签（保持原有关联关系）
        tags = [
            Tag(name='algorithm'),
            Tag(name='data-structure')
        ]

        # 保存所有对象
        db.session.bulk_save_objects(submissions + tags)
        db.session.commit()
        
        contest1 = Contest.query.filter_by(id = 1).first()
        contest1.update_problems(problem_ids=[1,2],current_user=self.users[0])

        # 生成测试token（实际项目应使用正式生成方法）
        self.tokens = {
            'admin': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxIiwic3ViIjoiMTEiLCJwb3dlciI6IjIiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiYWRtaW4ifQ.ZCCkJ0r0ghLvSEKViBY3MtOeBf_GgzJ3y7ZO9eTuvv8',
            'user': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoidXNlciJ9.NwUOdtcAs5KzOMtNiC8qZj4qad3OZ85f1_qqWH-GaDA',
            'creator': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiY3JlYXRvciJ9.mz4JKpGvW8MQGPHU20L3JiMTjbNpH6B26798NiCcNB8'
        }

    # 辅助方法
    def get_headers(self, token_key):
        return {'token': self.tokens[token_key]}
    
    def _read_test_code(self, filename):
        path = os.path.join(self.testcodepath, filename)
        with open(path, 'r') as f:
            return f.read()
    # 测试用例分割线 --------------------------------------------------------

    

    def test_submit_cpp_ac(self):
        """测试C++正确提交（Accepted）"""
        data = {
            'problem_id': 1,
            'contest_id': 1,
            'code': self._read_test_code('test_cpp_ac.txt'),
            'language': 'cpp'
        }
        
        resp = self.client.post('/api/problem/submit', 
                              json=data, 
                              headers=self.get_headers('user'))
        self.assertEqual(resp.status_code, 200)
        
        submission_id = int(resp.json['OK'].split('=')[1].split(',')[0].strip())
        submission = Submission.query.filter_by(id=submission_id).first()
        
        print(f"test ce_info = {submission.compile_error_info}")
        self.assertEqual(submission.status, 'Accepted')
        problem = Problem.query.filter_by(id=1).first()
        self.assertEqual(problem.submit_num, 1)
        self.assertEqual(problem.accept_num, 1)

    def test_submit_python_ac(self):
        """测试Python正确提交（Accepted）"""
        data = {
            'problem_id': 1,
            'contest_id': 1,
            'code': self._read_test_code('test_python_ac.txt'),
            'language': 'python'
        }
        
        resp = self.client.post('/api/problem/submit', 
                              json=data, 
                              headers=self.get_headers('user'))
        self.assertEqual(resp.status_code, 200)
        
        submission_id = int(resp.json['OK'].split('=')[1].split(',')[0].strip())
        submission = Submission.query.filter_by(id=submission_id).first()
        
        self.assertEqual(submission.status, 'Accepted')
        problem = Problem.query.filter_by(id=1).first()
        self.assertEqual(problem.submit_num, 1)  # 接续前一个测试
        self.assertEqual(problem.accept_num, 1)

    def test_submit_cpp_tle(self):
        """测试C++错误答案（WrongAnswer）"""
        data = {
            'problem_id': 1,
            'contest_id': 1,
            'code': self._read_test_code('test_cpp_tle.txt'),
            'language': 'cpp'
        }
        
        resp = self.client.post('/api/problem/submit',
                              json=data,
                              headers=self.get_headers('user'))
        
        self.assertEqual(resp.status_code, 200)
        submission_id = int(resp.json.get("submission_id"))
        submission = Submission.query.filter_by(id=submission_id).first()
        self.assertEqual(submission.status, 'TimeLimitExceeded')
        
        problem = Problem.query.filter_by(id=1).first()
        self.assertEqual(problem.submit_num, 1)
        self.assertEqual(problem.accept_num, 0)

    def test_submit_python_ce(self):
        """测试Python编译错误（CompileError）"""
        data = {
            'problem_id': 1,
            'contest_id': 1,
            'code': self._read_test_code('test_python_ce.txt'),
            'language': 'python'
        }
        
        resp = self.client.post('/api/problem/submit',
                              json=data,
                              headers=self.get_headers('user'))
        
        self.assertEqual(resp.status_code, 200)
        submission_id = int(resp.json.get("submission_id"))
        submission = Submission.query.filter_by(id=submission_id).first()
        
        self.assertEqual(submission.status, 'RuntimeError')
        
        problem = Problem.query.filter_by(id=1).first()
        self.assertEqual(problem.submit_num, 1)
        self.assertEqual(problem.accept_num, 0)

    def test_submit_cpp_ce(self):
        """测试C++编译错误（CompileError）"""
        data = {
            'problem_id': 1,
            'contest_id': 1,
            'code': self._read_test_code('test_cpp_ce.txt'),
            'language': 'cpp'
        }
        
        resp = self.client.post('/api/problem/submit',
                              json=data,
                              headers=self.get_headers('user'))
        
        self.assertEqual(resp.status_code, 200)
        submission_id = int(resp.json.get("submission_id"))
        submission = Submission.query.filter_by(id=submission_id).first()
        
        self.assertEqual(submission.status, 'CompileError')
        self.assertIn("src.cpp", submission.compile_error_info)
        
        problem = Problem.query.filter_by(id=1).first()
        self.assertEqual(problem.submit_num, 0)
        self.assertEqual(problem.accept_num, 0)