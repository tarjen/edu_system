from flask import Flask,jsonify,request
from online_judge import app
from online_judge.models.problems import Problem
from online_judge.models.submissions import Submission
from online_judge.models.contests import Contest,ContestUser
import json

@app.route('/api/contest/filter', methods=['POST'])
def filter_contests():
    """
    根据POST请求中的JSON参数过滤竞赛
    
    Args:
        (通过JSON Body传递参数)
        title (str, 可选): 竞赛标题模糊搜索关键词
        holder_name (str, 可选): 主办方名称精确匹配
    
    Returns:
        list[dict]: 过滤后的竞赛数据列表
    """

    data = request.get_json()
    title_query = data.get('title')
    holder_query = data.get('holder_name')

    filtered_contests = Contest.query

    if title_query:
        filtered_contests = filtered_contests.filter(Contest.title.ilike(f'%{title_query}%'))
        
    if holder_query:
        filtered_contests = filtered_contests.filter(Contest.holder_name == holder_query)

    return jsonify([{
        'contest_id': contest.id,
        'contest_title': contest.title,
        'holder_id': contest.holder_id,
        'start_time': contest.start_time,
        'end_time': contest.end_time
    } for contest in filtered_contests.all()])

@app.route('/api/contest/getinfo/<int:contest_id>', methods=['GET'])
def get_contestinfo(contest_id):
    """
    Show contest info for a contest_id
    
    Args:
        contest_id (int): The ID of the contest.
        
    Returns:
        dict: A dictionary containing contest information.
    """
    #TODO JWT_TOKEN

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

@app.route('/api/contest/get_contest_user_solved_problem/<int:contest_id>', methods=['POST'])
def get_contest_user_solved_problem(contest_id):
    """
        Show the user solved problem for the given contest
        Args:
        Returns:
    """
    #JWT_TOKEN and get user_id
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
    """
        Show all participants for the given contest 
        Args:
        Returns:
    """
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    

    contest_users = ContestUser.query.filter_by(contest_id=contest_id).all()
    user_list = []
    for user in contest_users:
        user_list.append(user.user_id)
    return jsonify(user_list)

@app.route('/api/contest/get_all_submission/<int:contest_id>', methods=['GET'])
def get_contest_all_submission(contest_id):
    """
        Show all the submisson(no code) for the given contest 
        Args:
        Returns:
    """
    #TODO JWT_TOKEN and check user
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

@app.route('/api/contest/get_contest_user_submission/<int:contest_id>', methods=['POST'])
def get_contest_user_submission(contest_id):
    """
        Show the user's all submission for the given contest
        Args:
        Returns:
    """
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