import os
import sys

from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config["JWT_SECRET_KEY"] = 123456
jwt = JWTManager(app)

@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # 获取 Token 中的身份信息
    # current_user = get_jwt_identity()
    # 获取 Token 中的所有声明
    # claims = get_jwt()
    # role = claims.get("role")  # 获取自定义声明（如用户角色）
    return jsonify({
        "message": "你已成功访问受保护的路由",
        # "current_user": current_user,
        # "role": role,
    }), 200


from online_judge import *

def test_token_validity(token):
    with app.test_client() as client:
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/protected', headers=headers)
        return response
    
@app.route("/test", methods=["GET"])
def test():
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxIiwiZXhwIjoxNzQwMDI1NTg4fQ.vBiPBUCaUF_wcCSa2hxvFmXXllt8ptj-ubdoUeZHsvY"
    response = test_token_validity(token)
    # return token
    return response.json