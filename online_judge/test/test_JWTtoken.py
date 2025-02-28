import unittest
import json
from online_judge import app

class CustomHeaderJWTTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True


        self.client = app.test_client()
        self.valid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxIiwic3ViIjoiMTEiLCJwb3dlciI6MiwiZXhwIjoxNzcyMTE5MDgwLCJ1c2VybmFtZSI6IkFETUlOIn0.ZtVxfa_kyEnVcEb_XarhQS_CeRZhx8CkOL1GFD98-yQ"
    
    def test_valid_token_access(self):
        """测试有效令牌的正常访问"""
        headers = {'token': self.valid_token}
        # headers = {"Authorization": f"Bearer {self.valid_token}"}
        # print(headers)
        response = self.client.get('/protected', headers=headers)
        print(response.data)  # 查看具体错误信息
        # 验证状态码
        self.assertEqual(response.status_code, 200)
        
        # 解析响应数据
        data = json.loads(response.data)
        
        # 验证核心字段
        self.assertEqual(data['user_id'], "1")
        self.assertEqual(data['power'], 2)
        self.assertEqual(data['user_name'], "ADMIN")

    def test_invalid_token_signature(self):
        """测试签名错误的令牌"""
        # 构造错误签名令牌(修改最后5个字符)
        invalid_token = self.valid_token[:-5] + "ABCDE"
        headers = {'token': invalid_token}
        response = self.client.get('/protected', headers=headers)
        
        self.assertNotEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
