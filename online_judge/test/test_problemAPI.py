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

class ProblemAPITestCase(unittest.TestCase):
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

    def test_get_public_problem(self):
        """测试获取公开题目详情"""
        headers = self.get_headers('user')
        response = self.client.post('/api/problem/statement/get',
                                  json={'problem_id': 1},
                                  headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['title'], "Problem 1")
        self.assertEqual(data['memory_limit'], 256)

    def test_get_private_problem_without_permission(self):
        """测试无权限获取私有题目"""
        # 将题目设为私有
        problem = Problem.query.filter_by(id=1).first()
        problem.is_public = False
        db.session.commit()

        headers = self.get_headers('user')
        response = self.client.post('/api/problem/statement/get',
                                  json={'problem_id': 1},
                                  headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_create_problem_success(self):
        """测试成功创建题目"""
        headers = self.get_headers('admin')
        data = {
            "title": "New Problem",
            "time_limit": 2,
            "memory_limit": 512,
            "statement": "Description",
            "difficulty": 2,
            "is_public": True,
            "tags": ["math"]
        }
        response = self.client.post('/api/problem/create',
                                  json=data,
                                  headers=headers)
        self.assertEqual(response.status_code, 201)
        new_id = response.json['problem_id']
        
        # 验证数据库记录
        problem = Problem.query.filter_by(id=new_id).first()
        self.assertEqual(problem.title, "New Problem")
        self.assertEqual(len(problem.tags), 1)

        headers = self.get_headers('admin')
        update_data = {
            "title": "Updated Title",
            "time_limit": 1500,
            "memory_limit": 512,
            "statement": "New content",
            "tags": ["algorithm"]
        }
        response = self.client.post(f'/api/problem/statement/update/{new_id}',
                                  json=update_data,
                                  headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # 验证数据库更新
        problem = Problem.query.filter_by(id=new_id).first()
        self.assertEqual(problem.title, "Updated Title")
        self.assertEqual(problem.memory_limit, 512)

    def test_create_problem_missing_required_field(self):
        """测试缺少必填字段创建题目"""
        headers = self.get_headers('admin')
        invalid_data = {
            "title": "Incomplete Problem",
            "time_limit": 1000,
            # 缺少memory_limit等字段
        }
        response = self.client.post('/api/problem/create',
                                  json=invalid_data,
                                  headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_update_problem_without_ownership(self):
        """测试非所有者更新题目"""
        headers = self.get_headers('user')
        response = self.client.post('/api/problem/statement/update/1',
                                  json={"title": "Hacked"},
                                  headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_upload_testdata_success(self):
        """测试新建题目并成功上传测试数据"""
        # 先创建新题目
        create_headers = self.get_headers('admin')
        create_data = {
            "title": "New Problem",
            "time_limit": 1,
            "memory_limit": 256,
            "statement": "Description",
            "difficulty": 1,
            "is_public": True,
            "tags": []
        }
        create_res = self.client.post('/api/problem/create',
                                    json=create_data,
                                    headers=create_headers)
        self.assertEqual(create_res.status_code, 201)
        new_problem_id = create_res.json['problem_id']

        # 生成测试ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('1.in', 'input')
            zf.writestr('1.out', 'output')
            zf.writestr('2.in', 'input2')
            zf.writestr('2.out', 'output2')
        zip_buffer.seek(0)
        
        # 使用新题目ID上传数据
        headers = self.get_headers('admin')
        response = self.client.post(f'/api/problem/data/update/{new_problem_id}',
                                data={'file': (zip_buffer, 'testdata.zip')},
                                headers=headers,
                                content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['testcase_count'], 2)

        # 验证数据库记录
        problem = Problem.query.filter_by(id=new_problem_id).first()
        self.assertEqual(problem.title, "New Problem")

    def test_upload_invalid_testdata(self):
        """测试新建题目后上传非法数据"""
        # 创建新题目
        create_headers = self.get_headers('admin')
        create_data = {
            "title": "Problem 2",
            "time_limit": 2,
            "memory_limit": 512,
            "statement": "Another problem",
            "difficulty": 2,
            "is_public": False,
            "tags": ["math"]
        }
        create_res = self.client.post('/api/problem/create',
                                    json=create_data,
                                    headers=create_headers)
        self.assertEqual(create_res.status_code, 201)
        new_problem_id = create_res.json['problem_id']

        # 生成无效ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('1.in', 'input')  # 缺少.out文件
        zip_buffer.seek(0)
        
        # 使用新题目ID上传
        headers = self.get_headers('admin')
        response = self.client.post(f'/api/problem/data/update/{new_problem_id}',
                                data={'file': (zip_buffer, 'bad.zip')},
                                headers=headers,
                                content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        
        # 验证题目元数据未改变
        problem = Problem.query.filter_by(id=new_problem_id).first()
        self.assertEqual(problem.memory_limit, 512)

if __name__ == '__main__':
    unittest.main()