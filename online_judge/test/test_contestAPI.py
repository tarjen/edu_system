import unittest,json
from datetime import datetime
from flask import Flask
from online_judge import db,app
from online_judge.models import Contest, Problem, Submission, Tag, ContestUser

class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

class ContestAPITestCase(unittest.TestCase):
    def setUp(self):
        # 创建全新的Flask应用实例（避免全局状态污染）
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
    
    # 测试用例分割线 --------------------------------------------------------

    def test_filter_contests(self):
        """测试比赛过滤接口 /api/contest/filter"""
        # 测试标题搜索
        resp = self.client.post('/api/contest/filter', json={'title': 'Admin'}, headers = self.get_headers('admin'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['contest_title'], "Admin's Contest")

    def test_get_contest_info(self):
        """测试获取比赛信息接口 /api/contest/getinfo"""
        # 管理员访问自己的比赛
        resp = self.client.get('/api/contest/getinfo/1', 
                           headers=self.get_headers('admin'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('problem_ids', resp.json)
        
        # 普通用户访问他人比赛
        resp = self.client.get('/api/contest/getinfo/2',
                           headers=self.get_headers('user'))
        self.assertEqual(resp.status_code, 404)

    def test_update_contest_users(self):
        """测试更新参赛用户接口 /api/contest/update_contest_user"""
        test_data = {'users': [2, 3]}
        
        # 管理员更新比赛用户
        resp = self.client.post('/api/contest/update_contest_user/1',
                            json=test_data,
                            headers=self.get_headers('admin'))
        self.assertEqual(resp.status_code, 200)
        self.assertListEqual(resp.json['added'], [3])
        
        # 验证数据库
        users = ContestUser.query.filter_by(contest_id=1).all()
        self.assertEqual(len(users), 2)

    def test_contest_problem_operations(self):
        """测试题目管理接口 /api/contest/update_problems/1"""
        # 管理员添加题目
        resp = self.client.post('/api/contest/update_problems/1',
                            json={'problem_ids': [1]},
                            headers=self.get_headers('admin'))
        self.assertEqual(resp.status_code, 200)
        self.assertListEqual(resp.json['problem_ids'], [1])

    def test_user_submissions(self):
        """测试获取用户提交记录接口 /api/contest/get_contest_user_submission"""
        # 先创建测试提交记录

        resp = self.client.get('/api/contest/get_contest_user_submission/1',
                           headers=self.get_headers('user'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 2)

        sub = Submission(user_id=2, contest_id=1, problem_id=1,code="code",language="cpp",submit_time=datetime(2025, 1, 1, 9, 0, 0))
        sub.save()
        
        resp = self.client.get('/api/contest/get_contest_user_submission/1',
                           headers=self.get_headers('user'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 3)

    def test_create_contest(self):
        """测试创建比赛接口 /api/contests"""
        valid_data = {
            "title": "New Contest",
            "start_time": "Wed, 26 Feb 2025 08:00:00 GMT",
            "end_time": "Wed, 27 Feb 2025 08:00:00 GMT"
        }
        
        # 管理员创建比赛
        resp = self.client.post('/api/contests',
                            json=valid_data,
                            headers=self.get_headers('admin'))
        self.assertEqual(resp.status_code, 201)
        self.assertIn('contest', resp.json)

    def test_update_contest_info(self):
        """测试更新比赛信息接口 /api/contest/update_contest_info"""
        update_data = {'title': 'Updated Title'}
        
        # 创建者更新自己的比赛
        resp = self.client.post('/api/contest/update_contest_info/2',
                            json=update_data,
                            headers=self.get_headers('creator'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['OK'], "update success")

    def test_solved_problems(self):
        """测试获取已解决题目接口 /api/contest/get_contest_user_solved_problem"""
        # 先创建测试数据
        sub = Submission.query.filter_by(contest_id=1,user_id=2,problem_id=1).first()
        sub.update_result_from_pending(status="Accepted",time_used = 1,memory_used = 2)
        sub.save()

        resp = self.client.post('/api/contest/get_contest_user_solved_problem/1',
                            headers=self.get_headers('user'))
        self.assertEqual(resp.status_code, 200)
        self.assertListEqual(resp.json, [])

    def test_authorization(self):
        """测试所有接口的授权验证"""
        # 测试无token访问
        endpoints = [
            ('GET', '/api/contest/getinfo/1'),
            ('POST', '/api/contest/update_contest_user/1'),
            ('POST', '/api/contests')
        ]
        
        for method, endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                if method == 'GET':
                    resp = self.client.get(endpoint)
                else:
                    resp = self.client.post(endpoint)
                self.assertEqual(resp.status_code, 401)
    def test_get_all_submissions(self):
        """测试获取比赛全部提交记录"""
        headers = self.get_headers('admin')
        resp = self.client.get('/api/contest/get_all_submission/1', headers=headers)
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 2)
        
        # 验证返回字段
        first_sub = resp.json[0]
        self.assertIn('problem_id', first_sub)
        self.assertIn('user_id', first_sub)
        self.assertEqual(first_sub['status'], 'Pending')
    
    def test_user_submissions_filter(self):
        """测试获取用户自己的提交记录"""
        headers = self.get_headers('user')
        resp = self.client.get('/api/contest/get_contest_user_submission/1', headers=headers)
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 2)
        
        # 验证只能看到自己的提交
        user_ids = {s['user_id'] for s in resp.json}
        self.assertEqual(user_ids, {2})
    
    def test_submission_status_update(self):
        """测试提交状态更新后的可见性"""
        # 先更新一个提交的状态
        sub = Submission.query.filter_by(contest_id=1,user_id=2,problem_id=1).first()
        sub.update_result_from_pending(status="RuntimeError",time_used = 1,memory_used = 2)
        sub.save()
        
        headers = self.get_headers('admin')
        resp = self.client.get('/api/contest/get_all_submission/1', headers=headers)
        
        updated_sub = next(s for s in resp.json if s['submission_id'] == 1)
        self.assertEqual(updated_sub['status'], 'RuntimeError')
    
    def test_contest_submission_permission(self):
        """测试非参赛用户访问提交记录的权限"""
        
        resp = self.client.get('/api/contest/get_all_submission/1', headers=self.get_headers('creator'))
        self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
