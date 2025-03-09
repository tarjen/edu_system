import unittest,json,io,zipfile
from datetime import datetime,timedelta
from flask import Flask
from dotenv import load_dotenv
from online_judge import db,app
from online_judge.models import Contest, Problem, Submission, Tag, ContestUser

class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

class InContestTestCase(unittest.TestCase):
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
        self.users = [
            User(id=1, username='admin', power=2),
            User(id=2, username='user', power=1),
            User(id=3, username='creator', power=1)
        ]
        
        contests = [
            Contest(
                title="Admin's Contest",
                
                start_time=datetime(2025, 1, 1, 7, 0, 0),  
                end_time=datetime(2025, 1, 2, 7, 0, 0),    
                holder_id=1,
                holder_name="admin"  # 对应User.username
            )
        ]

        db.session.bulk_save_objects(contests)
        db.session.commit()

        # 创建测试题目（完全符合Problem构造函数）
        problems = [
            Problem(
                title="Problem 1",
                statement="Statement 1",
                user_id=1,
                user_name="admin",  # 对应User.username
                difficulty=1,
                is_public=True,
                time_limit=2,    # 默认值
                memory_limit=256    # 默认值
            )
        ]
        db.session.bulk_save_objects(problems)
        db.session.commit()
        # 创建测试提交记录（完全符合Submission构造函数）

        # 创建ContestUser测试数据
        contest_users = [
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

        # 创建标签（保持原有关联关系）
        tags = [
            Tag(name='algorithm'),
            Tag(name='data-structure')
        ]

        # 保存所有对象
        db.session.bulk_save_objects(tags)
        db.session.commit()
        
        contest1 = Contest.query.filter_by(id = 1).first()
        contest1.update_problems(problem_ids=[1],current_user=self.users[0])

        # 生成测试token（实际项目应使用正式生成方法）
        self.tokens = {
            'admin': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxIiwic3ViIjoiMTEiLCJwb3dlciI6IjIiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiYWRtaW4ifQ.ZCCkJ0r0ghLvSEKViBY3MtOeBf_GgzJ3y7ZO9eTuvv8',
            'user': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoidXNlciJ9.NwUOdtcAs5KzOMtNiC8qZj4qad3OZ85f1_qqWH-GaDA',
            'creator': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiY3JlYXRvciJ9.mz4JKpGvW8MQGPHU20L3JiMTjbNpH6B26798NiCcNB8'
        }

    # 辅助方法
    def get_headers(self, token_key):
        return {'token': self.tokens[token_key]}
    
    # 测试用例分割线 --------------------------------------------------------

    def test_first_ac_submission(self):
        """测试首次正确提交后的分数计算"""
        data = {
            'problem_id': 1,
            'contest_id': 1,
            'code': 'a, b = map(int, input().split())\nprint(a+b)',
            'language': 'python',
            'submit_time': datetime(2025, 1, 1, 9, 0, 0)  
        }
        
        # 用户首次提交AC
        resp = self.client.post('/api/problem/submit', 
                              json=data, 
                              headers=self.get_headers('user'))
        
        self.assertEqual(resp.status_code, 200)
        # 验证分数记录
        contest_user = ContestUser.query.filter_by(contest_id=1, user_id=2).first()
        details = contest_user.get_score_details()
        
        self.assertEqual(details['1']['solve_time'], 120)  # 比赛开始后2小时提交
        self.assertEqual(details['1']['attempts'], 0)
        
        # 验证排行榜
        ranklist = Contest.query.filter_by(id=1).first().get_ranklist()
        self.assertEqual(ranklist[0]['user_id'], 2)  # 提交用户应排第一
        self.assertEqual(ranklist[0]['score'], 1)
        self.assertEqual(ranklist[0]['penalty'], 120)

    def test_multiple_attempts_before_ac(self):
        """测试多次错误后正确提交的罚时计算"""
        # 第一次WA提交
        self.client.post('/api/problem/submit', json={
            'problem_id': 1,
            'contest_id': 1,
            'code': 'print(1+2)',  # 错误代码
            'language': 'python',
            'submit_time': datetime(2025, 1, 1, 8, 0, 0)  
        }, headers=self.get_headers('user'))
        
        # 第二次AC提交
        resp2 = self.client.post('/api/problem/submit', json={
            'problem_id': 1,
            'contest_id': 1,
            'code': 'a, b = map(int, input().split())\nprint(a+b)',
            'language': 'python',
            'submit_time': datetime(2025, 1, 1, 9, 0, 0)  
        }, headers=self.get_headers('user'))
        
        submission_id =resp2.json.get('submission_id')
        submission =  Submission.query.filter_by(id=submission_id).first()
        print(f"test === status={submission.status}")
        contest_user = ContestUser.query.filter_by(contest_id=1, user_id=2).first()
        details = contest_user.get_score_details()
        
        self.assertEqual(details['1']['attempts'], 1)  # 包含一次错误尝试
        self.assertEqual(details['1']['solve_time'], 120)  # 假设第二次提交在120分钟时
        
        # 验证总罚时：120 + 1*20 = 140
        score, penalty = contest_user.calculate_score([1])
        self.assertEqual(penalty, 140)

    def test_ranking_order(self):
        """测试多个用户的排行榜排序"""
        # 用户2提交AC
        self.client.post('/api/problem/submit', json={
            'problem_id': 1,
            'contest_id': 1,
            'code': 'a, b = map(int, input().split())\nprint(a+b)',
            'language': 'python',
            'submit_time': datetime(2025, 1, 1, 10, 0, 0)  

        }, headers=self.get_headers('user'))
        
        # 用户1提交AC（更早时间）
        self.client.post('/api/problem/submit', json={
            'problem_id': 1,
            'contest_id': 1,
            'code': 'a, b = map(int, input().split())\nprint(a+b)',
            'language': 'python',
            'submit_time': datetime(2025, 1, 1, 9, 0, 0)  # 提前1小时提交
        }, headers=self.get_headers('admin'))
        
        ranklist = Contest.query.filter_by(id=1).first().get_ranklist()
        
        # 用户1应排第一（相同分数，罚时更少）
        self.assertEqual(ranklist[0]['user_id'], 1)
        self.assertEqual(ranklist[0]['penalty'], 120)  # 60分钟 + 0罚时
        self.assertEqual(ranklist[1]['user_id'], 2)

    def test_compile_error_handling(self):
        """测试编译错误不计入尝试次数"""
        # 提交包含语法错误的代码
        self.client.post('/api/problem/submit', json={
            'problem_id': 1,
            'contest_id': 1,
            'code': 'print("missing parenthesis"',
            'language': 'cpp',
            'submit_time': datetime(2025, 1, 1, 9, 0, 0) 
        }, headers=self.get_headers('user'))
        
        contest_user = ContestUser.query.filter_by(contest_id=1, user_id=2).first()
        details = contest_user.get_score_details()
        
        # 应不记录尝试次数
        self.assertNotIn('1', details)  # 或 attempts保持0
        self.assertEqual(contest_user.calculate_score([1])[0], 0)

    def test_submission_outside_contest_time(self):
        """测试比赛时间外的提交不计分"""
        # 提交时间设置为比赛结束后
        with app.test_request_context():
            data = {
                'problem_id': 1,
                'contest_id': 1,
                'code': 'a, b = map(int, input().split())\nprint(a+b)',
                'language': 'python',
                'submit_time': datetime(2025, 1, 3, 8, 0, 0)  # 比赛结束后
            }
            
            resp = self.client.post('/api/problem/submit', 
                                  json=data, 
                                  headers=self.get_headers('user'))
            
            submission = Submission.query.filter_by(id=resp.json['submission_id']).first()
            self.assertEqual(submission.status, 'Accepted')
            
            # 验证分数未更新
            contest_user = ContestUser.query.filter_by(contest_id=1, user_id=2).first()
            self.assertEqual(contest_user.calculate_score([1])[0], 0)