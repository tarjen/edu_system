from flask import Flask,jsonify
from online_judge import app
from online_judge.models.problems import Problem,Contest,ContestUser
from online_judge.models.submissions import Submission
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

@app.route('/api/contest/get_all_user/<int:contest_id>', methods=['GET'])
def get_contest_all_user(contest_id):
    contestuser = Contest.query.filter_by(id=contest_id).first()    
    if contestuser is None:
        return jsonify({"error": "contest or problem not found"}), 404    

    contest_users = ContestUser.query.filter_by(contest_id=contest_id).all()
    user_list = []
    for user in contest_users:
        user_list.append(user.user_id)
    return jsonify(user_list)

@app.route('/api/contest/get_all_submission/<int:contest_id>', methods=['GET'])
def get_contest_all_submission(contest_id):
    contestuser = Contest.query.filter_by(id=contest_id).first()    
    if contestuser is None:
        return jsonify({"error": "contest or problem not found"}), 404    

    submissions = Submission.query.filter_by(contest_id=contest_id).all()
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

@app.route('/api/contest/get_contest_user_submission/<int:contest_id>/<int:user_id>', methods=['GET'])
def get_contest_user_solved_problem(contest_id,user_id):
    contestuser = ContestUser.query.filter_by(contest_id=contest_id,user_id=user_id).first()    
    if contestuser is None:
        return jsonify({"error": "contest or problem not found"}), 404    

    submissions = Submission.query.filter_by(contest_id=contest_id,user_id=user_id).all()
    submission_list = []

    for submission in submissions:
        submission_data = {
            'problem_id': submission.problem_id,
            'submit_time': submission.submit_time,
            'language': submission.language,
            'status': submission.status,
            'time_used': submission.time_used,
            'memory_used': submission.memory_used
        }

        submission_list.append(submission_data)

    return jsonify(submission_list)