import os
import sys

from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS

app = Flask(__name__)

# CORS(app, resources={r"/api/*": {"origins": ["http://59.79.9.18:8081"]}})  # 允许指定前端地址跨域
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Hello from Flask!"})


CORS(app) 
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config["JWT_SECRET_KEY"] = '123456'
app.config['JWT_ALGORITHM'] = 'HS256'
app.config["JWT_DECODE_AUDIENCE"] = None  # 禁用aud验证

app.config["JWT_TOKEN_LOCATION"] = ["headers"]  # 必须声明从headers获取
app.config["JWT_HEADER_NAME"] = "token"         # 请求头字段名称
app.config["JWT_HEADER_TYPE"] = ""              # 禁用类型前缀(如Bearer)

db = SQLAlchemy(app)

jwt = JWTManager(app)

from .api import *
from .models import *
from .click import *
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    claims = get_jwt()
    return jsonify({
        "user_id": claims.get("aud"),
        "user_name": claims.get("username"),
        "power": claims.get("power")
    }), 200


