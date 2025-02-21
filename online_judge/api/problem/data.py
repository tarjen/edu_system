import os,zipfile

from flask import send_file

from flask import Flask,jsonify,request
from online_judge import app
from online_judge.models.problems import Problem
@app.route('/api/problem/data/get/<int:problem_id>', methods=['GET'])
def get_problem_data(problem_id):
    #TODO JWT_CHECK and check if the user allowed to use the problem

    problem = Problem.query.filter_by(problem_id=problem_id).first()
    if problem is None:
        return jsonify({"error": "Problem not found"}), 404    
    else:
        folder_path = os.path.join(os.getenv('PROBLEM_PATH'), str(problem_id), 'data', 'secret')
        zip_filename = f'problem_{problem_id}_data.zip'

        # 创建一个压缩文件对象
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # 将文件夹下的所有文件添加到压缩文件中
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))

        # 返回压缩文件给用户
        return send_file(zip_filename, as_attachment=True)

@app.route('/api/problem/data/update/<int:problem_id>', methods=['POST'])
def update_problem_data(problem_id):
    # TODO: JWT_CHECK and check if the user is allowed to edit the problem

    problem = Problem.query.filter_by(problem_id=problem_id).first()
    if problem is None:
        return jsonify({"error": "Problem not found"}), 404

    # 获取上传的文件
    uploaded_file = request.files['file']

    if uploaded_file:
        # 构建文件夹路径和压缩文件名
        folder_path = os.path.join(os.getenv('PROBLEM_PATH'), str(problem_id), 'data', 'secret')
        zip_filename = f'problem_{problem_id}_data.zip'
        zip_filepath = os.path.join(os.getenv('PROBLEM_PATH'), zip_filename)

        # 保存上传的文件
        uploaded_file.save(zip_filepath)

        # 解压文件
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(folder_path)

        # 删除上传的压缩文件
        os.remove(zip_filepath)

        return jsonify({"message": "Problem data updated successfully"}), 200
    else:
        return jsonify({"error": "No file uploaded"}), 400