from flask import Flask,jsonify,request
from online_judge import app
from online_judge.models.problems import Problem,Contest,ContestUser
import json

@app.route('/api/contest/update_contest_info/<int:contest_id>', methods=['GET'])
def update_contest_info(contest_id):
    # can't update time 
    data = request.get_json()
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    
    if 'title' in data:
        contest.title = data['title']
    if 'information' in data:
        contest.information = data['information']
    if 'problem_ids' in data:
        contest.problem_ids = data['problem_ids']
    contest_problems = contest.problem_ids.split(",")
    contest_problems_int = [int(id) for id in contest_problems]
    contest.update_problem(contest_problems_int)
    contest.save()
    return jsonify({"OK": "update success"})

@app.route('/api/contest/update_contest_user/<int:contest_id>', methods=['GET'])
def update_contest_user(contest_id):
    # TODO: add user to contest
    pass
