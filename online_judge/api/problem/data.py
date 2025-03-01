import os,zipfile

from flask import send_file

from flask import Flask,jsonify,request,logging
from online_judge import app,jwt_required,get_jwt
from online_judge.models import Problem
from online_judge.api import User

import os
import zipfile
import tempfile
import shutil
import re
from werkzeug.utils import secure_filename

@app.route('/api/problem/data/update/<int:problem_id>', methods=['POST'])
@jwt_required()
def update_problem_data(problem_id):
    """
    更新题目测试数据（需题目创建者权限）
    
    通过上传ZIP压缩包替换题目测试数据
    
    Args:
        problem_id (int): 路径参数，需要更新的题目ID
        file (File): POST表单文件字段，必须为ZIP格式的测试数据压缩包
                
    Returns:
        JSON响应:
        - 200 OK: {"OK": "Problem data updated successfully"}
        - 400 Bad Request: {"error": "错误描述"}
        - 403 Forbidden: {"error": "权限不足"}
        - 404 Not Found: {"error": "题目不存在"}

    Raises:
        OSError: 文件系统操作异常
        zipfile.BadZipFile: 损坏的ZIP文件

    Notes:
        1. ZIP文件结构示例:
           |
           |--1.in
           |--1.out
        2. 数据要求：从1开始编号，最多30个测试点，一个.in对应一个.out
    """
    # 获取当前用户
    current_user = User(get_jwt())

    # 查询题目
    problem = Problem.query.get(problem_id)
    if not problem:
        return jsonify({"error": "the problem is not available"}), 404

    # 权限验证
    if current_user.id != problem.user_id:
        return jsonify({"error": "the user is not permitted to update the problem"}), 403

    # 检查文件上传
    if 'file' not in request.files:
        return jsonify({"error": "no file"}), 400
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "empty filename"}), 400

    # 验证文件扩展名
    if not uploaded_file.filename.lower().endswith('.zip'):
        return jsonify({"error": "the upload_file is not .zip"}), 400

    # 准备目标目录
    data_dir = os.path.join(
        os.getenv('PROBLEM_PATH'),
        str(problem_id),
        'data',
        'secret'
    )

    try:
        # 创建临时工作区
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 保存上传文件
            temp_zip = os.path.join(tmp_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(temp_zip)

            # 验证ZIP文件完整性
            if not zipfile.is_zipfile(temp_zip):
                return jsonify({"error": "the zip file is not available"}), 400

            # 创建临时解压目录
            extract_dir = os.path.join(tmp_dir, 'extracted')
            os.makedirs(extract_dir)

            # 解压文件
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # 验证测试数据文件
            testcases = []
            for f in os.listdir(extract_dir):
                if re.match(r'^\d+\.in$', f):
                    case_id = f.split('.')[0]
                    out_file = f"{case_id}.out"
                    if not os.path.exists(os.path.join(extract_dir, out_file)):
                        return jsonify({"error": f"testcase_{case_id}缺少.out文件"}), 400
                    testcases.append(int(case_id))

            # 检查测试点数量和连续性
            testcases.sort()
            if not testcases:
                return jsonify({"error": "未找到有效测试数据"}), 400
                
            if testcases[0] != 1 or testcases[-1] > 30:
                return jsonify({"error": "测试点编号需从1开始且不超过30"}), 400

            if testcases != list(range(1, len(testcases)+1)):
                return jsonify({"error": "测试点编号不连续"}), 400

            # 清空旧数据
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
            os.makedirs(data_dir, exist_ok=True)

            # 移动新数据
            for item in os.listdir(extract_dir):
                src = os.path.join(extract_dir, item)
                dst = os.path.join(data_dir, item)
                shutil.move(src, dst)

            return jsonify({"OK": "data update success", "testcase_count": len(testcases)}), 200

    except PermissionError:
        return jsonify({"error": "文件权限错误"}), 500
    except Exception as e:
        logging.error(f"数据更新失败: {str(e)}")
        return jsonify({"error": "Failed"}), 500