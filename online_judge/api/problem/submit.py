from flask import Flask, request, jsonify
from online_judge import app
from online_judge.models.problems import Problem
from online_judge.models.contests import Contest,ContestUser
from online_judge.models.submissions import Submission

import time
def Judge(submission_id):
    #TODO judger
    pass

@app.route('/api/problem/submit', methods=['POST'])
def submit():
      # TODO JWT_TOKEN CHECK
    data = request.get_json()

    # 从请求体中提取所需的数据  
    user_id = data.get('user_id')
    problem_id = data.get('problem_id')
    contest_id = data.get('contest_id')
    code = data.get('code')
    language = data.get('language')

    problem = Problem.query.filter_by(id=problem_id).first()

    if problem is None or (problem.is_public == False and contest_id == -1):
        return jsonify({"error": "problem is not available"})    
    
    if contest_id != -1:
        contestuser = ContestUser.query.filter_by(contest_id=contest_id,problem_id=problem_id).first()
        if contestuser is None:
            return jsonify({"error": "the contest is not available for the user"})    
        if problem_id not in Contest.query.filter_by(id=contest_id).first().get_problems():
            return jsonify({"error": "the contest don't have this problem"})    
    submission = Submission(code=code,user_id=user_id,problem_id=problem_id,
                            submit_time=time.time())
    Judge(submission.id)
    return jsonify({"OK": f"submission_id = {submission.id},ok!"})

