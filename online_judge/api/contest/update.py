from flask import Flask,jsonify,request
from online_judge import app
from online_judge.models.problems import Problem
from online_judge.models.contests import Contest,ContestUser
import json

@app.route('/api/contest/update_contest_info/<int:contest_id>', methods=['POST'])
def update_contest_info(contest_id):
    # TODO check jwt_token and check admin
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    
    data = request.get_json()
    if 'title' in data:
        contest.title = data['title']
    if 'information' in data:
        contest.information = data['information']
    if 'problem_ids' in data:
        contest.problem_ids = data['problem_ids']
    contest_problems = contest.problem_ids.split(",")
    contest_problems_int = [int(id) for id in contest_problems]

    # check the problem whether availabe for the contest
    # availabe when 1. holder = problem_setter 2.admin
    for problem_id in contest_problems_int:
        problem = Problem.query.filter_by(id=problem_id).first()
        if not problem:
            return jsonify({"Failed": f"problem_id = {problem_id} not found"})
        if problem.is_public is False and problem.user_id != contest.holder_id:
            return jsonify({"Failed": f"problem_id = {problem_id} is not available for this contest"}) 
    contest.update_problem(contest_problems_int)
    contest.save()
    return jsonify({"OK": "update success"})

@app.route('/api/contest/update_contest_user/<int:contest_id>', methods=['POST'])
def update_contest_user(contest_id):
    # TODO: add user to contest
    pass
