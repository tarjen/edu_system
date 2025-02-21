import unittest

from online_judge import app
from flask import Flask,request,jsonify


class JWT_TestCase(unittest.TestCase):

    def setUp(self):
        app.config["JWT_SECRET_KEY"] = "123456"

    def tearDown(self):
        app.config.clear()

    def test_token_valid(self):
        app.url_map.comparator.match('/protect', method='GET')
        pass
    # 测试程序实例是否存在
    def test_app_exist(self):
        self.assertIsNotNone(app)

    # 测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])