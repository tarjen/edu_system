import unittest,json,io,zipfile
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv
from online_judge import db,app
from online_judge.models import Contest, Problem, Submission, Tag, ContestUser

class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

class CreateProblemTestCase(unittest.TestCase):
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

    def get_headers(self, token_key):
        return {'token': self.tokens[token_key]}

    def test_full_lifecycle(self):
        """测试A+B题目的完整流程"""
        # 步骤1：创建题目
        create_data = {
            "title": "A+B Problem",
            "time_limit": 1,
            "memory_limit": 256,
            "statement": "计算两个整数之和",
            "difficulty": 1,
            "is_public": True,
            "tags": ["math"]
        }
        
        # 管理员创建题目
        response = self.client.post(
            '/api/problem/create',
            json=create_data,
            headers=self.get_headers('admin')
        )
        self.assertEqual(response.status_code, 200)
        self.problem_id = response.json['problem_id']

        print(f"test ==== problem_id={self.problem_id}")
        
        # 验证数据库记录
        problem = Problem.query.filter_by(id=self.problem_id).first()
        self.assertEqual(problem.title, "A+B Problem")
        self.assertEqual([t.name for t in problem.tags], ["math"])

        # 步骤2：上传测试数据
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('1.in', '1 2')
            zf.writestr('1.ans', '3')
            zf.writestr('2.in', '-5 5')
            zf.writestr('2.ans', '0')
        zip_buffer.seek(0)

        response = self.client.post(
            f'/api/problem/data/update/{self.problem_id}',
            data={'file': (zip_buffer, 'data.zip')},
            headers=self.get_headers('admin'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['testcase_count'], 2)

        # 步骤3：测试各种提交
        test_cases = [
            {
                'code': 'print(sum(map(int, input().split())))',
                'language': 'python',
                'expected_status': 'Accepted'
            },
            {
                'code': 'a, b = map(int, input().split())\nprint(a - b)',
                'language': 'python',
                'expected_status': 'WrongAnswer'
            },
            {
                'code': 'invalid syntax!',
                'language': 'python',
                'expected_status': 'RuntimeError'
            }
        ]

        initial_stats = {
            'submit_num': Problem.query.filter_by(id=self.problem_id).first().submit_num,
            'accept_num': Problem.query.filter_by(id=self.problem_id).first().accept_num
        }

        for idx, case in enumerate(test_cases):
            with self.subTest(f"TestCase #{idx+1}: {case['expected_status']}"):
                # 提交代码
                submit_resp = self.client.post(
                    '/api/problem/submit',
                    json={
                        "problem_id": self.problem_id,
                        "contest_id": 0,
                        "code": case['code'],
                        "language": case['language']
                    },
                    headers=self.get_headers('user')
                )
                self.assertEqual(submit_resp.status_code, 200)
                
                # 验证计数器
                current_problem = Problem.query.filter_by(id=self.problem_id).first()
                expected_submit = initial_stats['submit_num'] + idx + 1
                self.assertEqual(current_problem.submit_num, expected_submit)
                submission_id = submit_resp.json.get("submission_id")
                submission=Submission.query.filter_by(id=submission_id).first()
                print(f"test ==== testcase{idx},ac_num={current_problem.accept_num},code={submission.code},status={submission.status}")
                # 验证通过数
                if case['expected_status'] == 'Accepted':
                    expected_accept = initial_stats['accept_num'] + 1
                    initial_stats['accept_num'] = expected_accept  # 更新基准
                self.assertEqual(current_problem.accept_num, initial_stats['accept_num'])

                # 验证提交记录状态（假设同步处理）
                submission = Submission.query.order_by(Submission.id.desc()).first()
                self.assertEqual(submission.status, case['expected_status'])