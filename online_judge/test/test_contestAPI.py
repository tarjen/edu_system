import unittest
from datetime import datetime
from flask import jsonify
from online_judge import app, db  # 替换为实际模块路径
from online_judge.models import Contest, Problem, Submission,Tag  # 替换为模型类路径

class ContestQueryAPI_TestCase(unittest.TestCase):
    def setUp(self):
        # 配置测试数据库
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app = app.test_client()
        
        # 初始化数据库结构
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # 注入测试数据
            contests = [
                Contest(title='Contest 1', start_time=datetime(2025, 2, 26, 8, 0, 0), end_time=datetime(2025, 2, 27, 8, 0, 0), holder_id=1, holder_name='Holder 1'),
                Contest(title='Contest 2', start_time=datetime(2025, 3, 5, 9, 0, 0), end_time=datetime(2025, 3, 6, 9, 0, 0), holder_id=2, holder_name='Holder 2'),
                Contest(title='Contest 3', start_time=datetime(2025, 3, 12, 10, 0, 0), end_time=datetime(2025, 3, 13, 10, 0, 0), holder_id=3, holder_name='Holder 3'),
                Contest(title='Contest 4', start_time=datetime(2025, 3, 19, 11, 0, 0), end_time=datetime(2025, 3, 20, 11, 0, 0), holder_id=4, holder_name='Holder 4'),
                Contest(title='Contest 5', start_time=datetime(2025, 3, 26, 12, 0, 0), end_time=datetime(2025, 3, 27, 12, 0, 0), holder_id=5, holder_name='Holder 5')
            ]

            # 生成 Problem 实例
            problems = [
                Problem(title='Problem 1', user_id=1, user_name='User 1',difficulty=1, time_limit=1, memory_limit=128, is_public=True),
                Problem(title='Problem 2', user_id=1, user_name='User 1',difficulty=2, time_limit=2, memory_limit=256, is_public=False),
                Problem(title='Problem 3', user_id=2, user_name='User 2',difficulty=1, time_limit=3, memory_limit=512, is_public=True),
                Problem(title='Problem 4', user_id=3, user_name='User 3',difficulty=1, time_limit=4, memory_limit=1024, is_public=True),
                Problem(title='Problem 5', user_id=3, user_name='User 3',difficulty=3, time_limit=5, memory_limit=2048, is_public=False)
            ]


            # 生成 Submission 实例
            submissions = [
                Submission(code='Submitted code for Problem 1', language='Python', user_id=1, problem_id=1, contest_id=0, submit_time=datetime.now()),
                Submission(code='Submitted code for Problem 2', language='C++', user_id=1, problem_id=2, contest_id=0, submit_time=datetime.now()),
                Submission(code='Submitted code for Problem 3', language='Rust', user_id=3, problem_id=3, contest_id=0, submit_time=datetime.now()),
                Submission(code='Submitted code for Problem 4', language='Python', user_id=4, problem_id=4, contest_id=0, submit_time=datetime.now()),
                Submission(code='Submitted code for Problem 5', language='C++', user_id=5, problem_id=5, contest_id=0, submit_time=datetime.now())
            ]

            # 生成Tag实例（基础标签库）
            tags = [
                Tag(name='algorithm'),
                Tag(name='dp'),
                Tag(name='ds'),
                Tag(name='graph'),
                Tag(name='string')
            ]

            db.session.bulk_save_objects(contests + problems + submissions + tags)

            # 生成ProblemTag实例（建立题目与标签的关联）
            # 建立标签关联（替代原ProblemTag）
            problem_relations = [
                (1, 'algorithm'),   # problem 1
                (1, 'dp'),          # problem 1
                (2, 'ds'),          # problem 2
                (3, 'graph'),       # problem 3
                (4, 'string'),      # problem 4
                (5, 'algorithm')    # problem 5
            ]

            for problem_id, tag_name in problem_relations:
                problem = Problem.query.filter_by(id=problem_id).first()
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag not in problem.tags:
                    problem.tags.append(tag)  # 通过关系字段直接操作

            # 保存所有数据

            db.session.commit()
            
    def test_get_contest_info(self):
        # 执行接口请求
        response = self.app.get('/api/contest/getinfo/1')
        
        # 验证响应状态
        self.assertEqual(response.status_code, 200)
        
        # 解析JSON响应
        data = response.get_json()
        
        # 验证核心字段
        self.assertEqual(data['contest_id'], 1)
        self.assertEqual(data['contest_title'], 'Contest 1')
        self.assertEqual(data['holder_name'], 'Holder 1')
        
        # 验证时间格式
        self.assertEqual('Wed, 26 Feb 2025 08:00:00 GMT', data['start_time'])
        
        # 验证关联数据（需根据实际模型关系调整）
        self.assertIsInstance(data['problem_ids'], list)
        self.assertIsInstance(data['ranklist'], list)

    def test_invalid_contest_id(self):
        # 测试无效ID场景
        response = self.app.get('/api/contest/getinfo/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.get_json())

    
    def test_filter_contests(self):
        """测试不同过滤条件下的比赛查询"""
        test_cases = [
            # (测试描述, 请求参数, 预期结果数量)
            ('空条件查询', {}, 5),
            ('标题模糊匹配', {'title': 'Contest'}, 5),
            ('标题精确匹配', {'title': 'Contest 1'}, 1),
            ('主办方精确匹配', {'holder_name': 'Holder 3'}, 1),
            ('组合条件查询', {'title': 'Contest', 'holder_name': 'Holder 2'}, 1),
            ('无结果条件', {'title': '不存在的比赛'}, 0)
        ]

        for desc, params, expected_count in test_cases:
            with self.subTest(desc=desc):
                response = self.app.post(
                    '/api/contest/filter',
                    json=params,
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                
                # 验证返回结果数量
                self.assertEqual(len(data), expected_count)
                
                # 验证字段完整性
                if data:
                    contest = data[0]
                    self.assertIn('contest_id', contest)
                    self.assertIn('contest_title', contest)
                    self.assertIn('holder_id', contest)
                    self.assertIn('start_time', contest)
                    self.assertIn('end_time', contest)
                
                # 验证精确匹配
                if 'holder_name' in params:
                    holder_names = {c['holder_id']: c['contest_title'] for c in data}
                    self.assertTrue(all(
                        'holder_name' not in c or c['holder_name'] == params['holder_name'] 
                        for c in data
                    ))


if __name__ == '__main__':
    unittest.main()
