from flask import Flask, request, jsonify
from online_judge import app,db,jwt_required,get_jwt
from online_judge.api import User
from online_judge.models.problems import Problem
from online_judge.models.contests import Contest,ContestUser
from online_judge.models.submissions import Submission
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
        match = re.search(r'CompileError\("(.*?)"\)', verdict, re.DOTALL)
        error_message = match.group(1)
        # 处理转义字符并过滤路径
        formatted_error = bytes(error_message, 'utf-8').decode('unicode_escape')
        # 使用正则表达式移除路径前缀（保留行号）
        formatted_error = re.sub(r'/.*(/src\.cpp)', r'src.cpp', formatted_error)
        # 处理行末的转义符
        return "CompileError",formatted_error.replace('\n', '\n').strip()
    else:
        lines = [line.strip() for line in verdict.split('\n') if line.strip()]
        return (lines[-1] if lines else ""),("")


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
            submission.update_result_from_pending("SystemError", ce_info="评测环境配置错误")
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
                "--output-format", "json"  # 要求评测器输出JSON格式
            ]

            # 执行评测
            result = subprocess.run(
                command,
                cwd=workspace_folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,  # 设置超时时间
                check=True   # 非零退出码触发异常
            )
            status,information = process_verdict(result.stdout)
            #TODO update TL&ML
            if status == "CompileError":
                # 清理路径信息
                submission.update_result_from_pending(
                    status,
                    time_used=0,
                    memory_used=0,
                    ce_info=information
                )
            else:
                submission.update_result_from_pending(
                    status,
                    time_used=0,
                    memory_used=0
                )

    except Exception as e:
        logging.critical(f"Critical error in Judge: {str(e)}", exc_info=True)
        if submission:
            submission.update_result_from_pending("SystemError", ce_info="system error")
    finally:
        # 确保数据库会话关闭
        db.session.remove()

@app.route('/api/problem/submit', methods=['POST'])
@jwt_required()
def submit():
    
    user = User(get_jwt())
    data = request.get_json()

    # 从请求体中提取所需的数据  
    problem_id = data.get('problem_id')
    contest_id = data.get('contest_id')
    code = data.get('code')
    language = data.get('language')

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
    submission = Submission(code=code,user_id=user.id,problem_id=problem_id,
                            submit_time=time.time())
    submission.save()
    Judge(submission.id)
    return jsonify({"OK": f"submission_id = {submission.id},ok!"})

