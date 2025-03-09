from flask import Flask, request, jsonify
from online_judge import app,db,jwt_required,get_jwt
from online_judge.api import User
from online_judge.models.problems import Problem
from online_judge.models.contests import Contest,ContestUser
from online_judge.models.submissions import Submission
from datetime import datetime
import pytz
import os,time
import re
import logging
import tempfile
import subprocess
from werkzeug.utils import secure_filename


def code_check(code,language):
    #TODO: check the code
    return True

def process_verdict(verdict):
    if "CompileError" in verdict:
        # 使用正则表达式匹配完整错误信息
        print(f"status =\n {verdict}")
        match = re.search(r'CompileError\("(.*?)"\)', verdict, re.DOTALL)
        error_message = match.group(1)
        # 处理转义字符并过滤路径
        formatted_error = bytes(error_message, 'utf-8').decode('unicode_escape')
        # 使用正则表达式移除路径前缀（保留行号）
        formatted_error = re.sub(r'/.*(/src\.cpp)', r'src.cpp', formatted_error)
        # 处理行末的转义符
        return "CompileError",formatted_error.replace('\n', '\n').strip(),0,0
    else:
        status = "SystemError"
        time_used = 0  # 单位：ms
        memory_used = 0 # 单位：bytes

        # 使用多行模式解析
        lines = [line.strip() for line in verdict.split('\n') if line.strip()]
        
        # 解析状态（取第三行）
        if len(lines) >= 3:
            status = lines[2]
        
        # 解析时间和内存（取第四行）
        if len(lines) >= 4:
            time_pattern = r"Max time:\s*([\d.]+)(ms|s)"
            mem_pattern = r"Max memory:\s*(\d+)\s*bytes"
            
            # 解析时间
            time_match = re.search(time_pattern, lines[3])
            if time_match:
                value, unit = time_match.groups()
                time_used = float(value) * 1000 if unit == "s" else float(value)
            
            # 解析内存
            mem_match = re.search(mem_pattern, lines[3])
            if mem_match:
                memory_used = int(mem_match.group(1))

        return status, "", time_used, memory_used  # 时间转为整数毫秒


def Judge(submission_id):
    """执行代码评测的核心函数
    
    Args:
        submission_id (int): 提交记录ID
    """
    
    try:
        # 获取提交记录
        submission = Submission.query.filter_by(id=submission_id).first()
        if not submission:
            logging.error(f"Submission {submission_id} not found")
            return

        # 校验评测环境
        workspace_folder = os.getenv('JUDGER_PATH')
        if not workspace_folder or not os.path.isdir(workspace_folder):
            logging.error(f"Invalid JUDGER_PATH: {workspace_folder}")
            submission.update_result_from_pending("SystemError", ce_info=f"Invalid JUDGER_PATH: {workspace_folder}")
            return

        # 创建临时工作区
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 准备源代码文件
            ext_mapping = {
                'cpp': 'cpp',
                'python': 'py'
            }
            file_ext = ext_mapping.get(submission.language, 'txt')
            src_filename = secure_filename(f"submission_{submission_id}.{file_ext}")
            src_path = os.path.join(tmp_dir, src_filename)
            
            try:
                with open(src_path, 'w', encoding='utf-8') as f:
                    f.write(submission.code)
            except Exception as e:
                logging.error(f"Failed to write code: {str(e)}")
                submission.update_result_from_pending("SystemError", ce_info="代码保存失败")
                return

            # 构建评测命令
            command = [
                os.path.join(workspace_folder, "target/debug/judger"),
                "judge",
                "--problem-slug", str(submission.problem_id),
                "--language", submission.language,
                "--src-path", src_path,
            ]

            # 执行评测
            result = subprocess.run(
                command,
                cwd=workspace_folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,  # 设置超时时间
                check=True   # 非零退出码触发异常
            )

            status, information, time_used, memory_used = process_verdict(result.stdout)
            # print(f"test_stderr = {result.stderr}")
            if status == "CompileError":
                # 清理路径信息
                submission.update_result_from_pending(
                    status=status,
                    time_used=0,
                    memory_used=0,
                    ce_info=information
                )
            else:
                submission.update_result_from_pending(
                    status=status,
                    time_used=time_used,
                    memory_used=memory_used,
                )

    except Exception as e:
        # logging.critical(f"Critical error in Judge: {str(e)}", exc_info=True)
        print(f"Critical error in Judge: {str(e)}")
    
        if submission:
            submission.update_result_from_pending("SystemError", ce_info="system error")
    finally:
        # 确保数据库会话关闭
        db.session.remove()

@app.route('/api/problem/submit', methods=['POST'])
@jwt_required()
def submit():
    """
    处理代码提交请求，支持比赛/练习两种模式。
    
    用户提交代码后，系统将进行合法性检查并触发自动评测。比赛提交需满足：
    - 用户在参赛名单中
    - 提交时间在比赛时段内
    - 题目属于比赛题目
    
    Args:
        
        JSON参数:
            problem_id (int): 必填，提交的题目ID
            code (str): 必填，用户提交的源代码
            language (str): 必填，编程语言（如python/cpp）
            contest_id (int, optional): 关联的比赛ID，默认0表示练习模式
            submit_time (str, optional): 提交时间（GMT格式），默认当前时间
            
    Returns:
        JSON: 包含提交ID的响应，格式：
            成功 (200):
                {
                    "OK": "submission_id = <id>,ok!",
                    "submission_id": <int>
                }
            错误时返回对应状态码和错误描述，例如：
    """
    user = User(get_jwt())
    data = request.get_json()

    # 参数验证
    required_fields = ['problem_id', 'code', 'language']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required parameters (problem_id/code/language)"}), 400

    # 提取并处理参数
    problem_id = data['problem_id']
    code = data['code']
    language = data['language']
    contest_id = data.get('contest_id', 0)  # 默认值0表示非比赛提交

    # 在路由函数中修改时间处理部分
    if 'submit_time' in data:
        try:
            # 解析RFC 1123格式时间
            submit_time = datetime.strptime(
                data['submit_time'], 
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            # 转换为UTC时区对象
            submit_time = submit_time.replace(tzinfo=pytz.UTC)
        except ValueError as e:
            return jsonify({
                "error": "Invalid datetime format, use 'Wed, 26 Feb 2025 08:00:00 GMT' format",
                "example": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            }), 400
    else:
        submit_time = datetime.now(pytz.UTC)  # 默认当前UTC时间


    problem = Problem.query.filter_by(id=problem_id).first()

    if not code_check(code,language):
        return jsonify({"error": "code is not availabe"}),404

    if problem is None or (problem.is_public == False and contest_id == 0):
        return jsonify({"error": "problem is not available"}),404
    
    if contest_id != 0:
        contestuser = ContestUser.query.filter_by(contest_id=contest_id,user_id=user.id).first()
        if contestuser is None:
            return jsonify({"error": "the contest is not available for the user"}),404   
        if problem_id not in Contest.query.filter_by(id=contest_id).first().get_problems():
            return jsonify({"error": "the contest don't have this problem"}),404
    submission = Submission(code=code,user_id=user.id,problem_id=problem_id,language=language,contest_id=contest_id,
                            submit_time=submit_time)
    submission.save()
    submission_id = submission.id    
    Judge(submission_id)
    return jsonify({"OK": f"submission_id = {submission_id},ok!","submission_id":submission_id}),200

