from flask import Flask,jsonify
from online_judge import app
from online_judge.models.problems import Problem,Contest,ContestUser
import json
@app.route('/api/contest/get_contest_list', methods=['GET'])
def get_contest_list():
    contests = Contest.query.all()  # 从数据库中获取所有的 contest 数据

    contest_list = []
    for contest in contests:
        contest_data = {
            'contest_id': contest.id,
            'contest_title': contest.title,
            'holder_id': contest.holder_id,
            'start_time': contest.start_time,
            'end_time': contest.end_time,
        }
        contest_list.append(contest_data)

    return jsonify(contest_list)

@app.route('/api/contest/getinfo/<int:contest_id>', methods=['GET'])
def get_contestinfo(contest_id):
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    contest_data = {
        'contest_id': contest.id,
        'contest_title': contest.title,
        'holder_id': contest.holder_id,
        'holder_name': contest.holder_name,
        'start_time': contest.start_time,
        'end_time': contest.end_time,
        'information': contest.information,
        'problem_ids': contest.get_problems(),
        'ranklist': contest.get_ranklist(),
    }

    return jsonify(contest_data)

@app.route('/api/contest/get_contest_user_solved_problem/<int:contest_id>/<int:user_id>', methods=['GET'])
def get_contest_user_solved_problem(contest_id,user_id):
    contestuser = ContestUser.query.filter_by(contest_id=contest_id,user_id=user_id).first()    
    if contestuser is None:
        return jsonify({"error": "contest or problem not found"}), 404    

    solved_problem = []
    problem_ids = Contest.query.filter_by(id=contest_id).first().get_problems()
    score_details = json.loads(contestuser.score_details)

    for problem_id in problem_ids:
        if problem_id in score_details:
            if score_details[problem_id]["solve_time"] != -1:
                solved_problem.append(problem_id)

    return jsonify(solved_problem)