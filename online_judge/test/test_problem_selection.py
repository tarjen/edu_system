import unittest
import random
from datetime import datetime, timedelta
from online_judge import app, db
from dotenv import load_dotenv
from online_judge.models import Problem, Tag, contest_problem

class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

class ProblemSelectionTest(unittest.TestCase):
    def setUp(self):
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

        self.setup_test_data()
        
    def setup_test_data(self):
        self.users = [
            User(id=1, username='admin', power=2),
            User(id=2, username='user', power=1),
            User(id=3, username='creator', power=1)
        ]
        # 预定义标签池
        self.tag_pool = ['算法', '数据结构', '动态规划', '图论', '字符串']
        for name in self.tag_pool:
            db.session.add(Tag(name=name))
        
        db.session.commit()
        # 生成50个测试题目
        for i in range(1, 51):
            # 随机生成标签组合（1-3个标签）
            tags = random.sample(self.tag_pool, k=random.randint(1,3))
            submit_num = random.randint(0, 100)
            accept_num = random.randint(0, submit_num)  # 确保 accept_num ≤ submit_num
            problem = Problem(
                title=f"Problem {i}",
                user_id=1,
                user_name="admin",
                statement=f"Statement {i}",
                difficulty=random.randint(1, 5),
                submit_num=submit_num,
                accept_num=accept_num,
                is_public=True
            )
            db.session.add(problem)
            # 关联标签
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                problem.tags.append(tag)
            
        
        db.session.commit()
        self.tokens = {
            'admin': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxIiwic3ViIjoiMTEiLCJwb3dlciI6IjIiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiYWRtaW4ifQ.ZCCkJ0r0ghLvSEKViBY3MtOeBf_GgzJ3y7ZO9eTuvv8',
            'user': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoidXNlciJ9.NwUOdtcAs5KzOMtNiC8qZj4qad3OZ85f1_qqWH-GaDA',
            'creator': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzIiwic3ViIjoiMTEiLCJwb3dlciI6IjEiLCJleHAiOjE3NzIxMTkwODAsInVzZXJuYW1lIjoiY3JlYXRvciJ9.mz4JKpGvW8MQGPHU20L3JiMTjbNpH6B26798NiCcNB8'
        }

    # 辅助方法
    def get_headers(self, token_key):
        return {'token': self.tokens[token_key]}
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        
        # 释放应用上下文
        self.app_context.pop()

    def test_any_tag_filter(self):
        """测试包含任意一个标签即可"""
        # 发送包含两个标签的请求
        response = self.client.post('/api/contest/select_problems', json={
            "average_difficulty": 2,
            "problem_count": 5,
            "average_accept_rate": 0.5,
            "average_used_times": 2,
            "allow_recent_used": True,
            "allowed_types": ["算法", "图论"],
        },headers=self.get_headers('admin'))
        
        # 验证结果
        selected_ids = response.json['selected_problems']
        print(f"seleced_ids = {selected_ids}")
        with app.app_context():
            for pid in selected_ids:
                problem = Problem.query.filter_by(id=pid).first()
                tags = {t.name for t in problem.tags}
                # 确认至少包含其中一个标签
                self.assertTrue(tags & {"算法", "图论"})

if __name__ == '__main__':
    unittest.main()