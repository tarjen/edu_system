from flask import Flask,jsonify,request
from online_judge import app
from online_judge.models.problems import Problem
from online_judge.models.submissions import Submission
from online_judge.models.contests import Contest

@app.route('/api/submission/filter', methods=['POST'])
def submission_filter():

    data = request.get_json()

    # 从请求体中提取所需的数据  
    user_id = data.get('user_id')
    problem_id = data.get('problem_id')
    contest_id = data.get('contest_id')
    language = data.get('language')
    
    # 构建基本查询
    query = Submission.query

    # 根据参数是否存在来动态构建查询条件
    if user_id:
        query = query.filter_by(user_id=user_id)
    if problem_id:
        query = query.filter_by(problem_id=problem_id)
    if contest_id:
        query = query.filter_by(contest_id=contest_id)
    if language:
        query = query.filter(language=language)

    submissions = query.all()
    submission_list = []

    for submission in submissions:
        submission_data = {
            'problem_id': submission.problem_id,
            'user_id': submission.user_id,
            'language': submission.language,
            'submit_time': submission.submit_time,
            'status': submission.status,
            'time_used': submission.time_used,
            'memory_used': submission.memory_used
        }

        submission_list.append(submission_data)

    return jsonify(submission_list)

@app.route('/api/submission/get/<int:submission_id>', methods=['GET'])
def get_submission(submission_id):
    submission = Submission.query.get(submission_id)

    if submission is None:
        return jsonify({"error": "Submission not found"}), 404
    else:
        submission_json = {
            "id": submission.id,
            "code": submission.code,
            "language": submission.language,
            "user_id": submission.user_id,
            "problem_id": submission.problem_id,
            "submit_time": submission.submit_time,
            "contest_id": submission.contest_id,
            "status": submission.status,
            "time_used": submission.time_used,
            "memory_used": submission.memory_used
        }

        return jsonify(submission_json)