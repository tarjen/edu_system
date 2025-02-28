from flask import Flask,jsonify,request
from online_judge import app,jwt,jwt_required,get_jwt
from online_judge.api import User
from online_judge.models.problems import Problem
from online_judge.models.submissions import Submission
from online_judge.models.contests import Contest,ContestUser
import json

@app.route('/api/contest/filter', methods=['POST'])
def filter_contests():
    """
    根据POST请求中的JSON参数过滤比赛
    
    Args:
        (通过JSON Body传递参数)
        title (str, 可选): 比赛标题模糊搜索关键词,支持部分匹配
        holder_name (str, 可选): 主办方名称精确匹配(区分大小写)
    
    Returns:
        list[dict]: 过滤后的比赛数据列表,每个字典包含:
            - contest_id (int): 比赛唯一标识符
            - contest_title (str): 比赛标题
            - holder_id (int): 主办用户ID
            - holder_name (str): 主办用户名称
            - start_time (str): 比赛开始时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - end_time (str): 比赛结束时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - information (str): 比赛描述信息
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
        'holder_name': contest.holder_name,
        'start_time': contest.start_time,
        'end_time': contest.end_time,
        'information': contest.information
    } for contest in filtered_contests.all()]),200

@app.route('/api/contest/getinfo/<int:contest_id>', methods=['GET'])
@jwt_required()
def get_contestinfo(contest_id):
    """
    (要求jwt_token)    
    根据GET请求中的 contest_id(int) 获得比赛具体信息
    
    Args:
        contest_id(int): 比赛编号
    
    Returns:
        dict: 比赛信息 (包含比赛id, 比赛标题, 管理人id, 管理人名字, 起始时间, 结束时间, 比赛信息, 题目编号, 排行榜)
        TODO: 加一个ranklist例子
    """
    user = User(get_jwt())
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    if not contest.is_allowed_view(user):
        return jsonify({"error": f"user_id = {user.id} can't view contest(id = {contest_id})"}), 404
      
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
@jwt_required()
def get_contest_user_solved_problem(contest_id):
    """
    获取指定比赛中用户已解决的题目列表
    
    Args:
        contest_id (int): 路径参数,比赛唯一标识符
        (通过JWT Token获取用户身份)
    
    Returns:
        list[int]: 用户已解决的题目ID列表,格式示例:
            [103, 105, 107]
        数据结构说明:
            - 每个元素为题目唯一标识符(整数)
            - 按实际解决顺序排序
    """
    user = User(get_jwt())
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    if not contest.is_allowed_view(user):
        return jsonify({"error": f"user_id = {user.id} can't view contest(id = {contest_id})"}), 404
    contestuser = ContestUser.query.filter_by(contest_id=contest_id,user_id=user.id).first()    

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
    获取指定比赛的所有参赛用户
    
    Args:
        contest_id (int): 路径参数,比赛唯一标识符
    
    Returns:
        list[int]: 参赛用户ID列表,格式示例:
            [1001, 1003, 1005]
        数据结构说明:
            - 每个元素为用户唯一标识符(整数)
            - 列表按用户加入比赛的时间排序
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
@jwt_required()
def get_contest_all_submission(contest_id):
    """
    获取所有在比赛中的所有提交记录
    
    Args:
        contest_id (int): 路径参数,比赛唯一标识符
        (通过JWT Token获取用户身份)
    
    Returns:
        list[dict]: 提交记录列表,每个字典包含:
            - submission_id (int): 提交唯一标识符
            - problem_id (int): 题目唯一标识符
            - submit_time (str): 提交时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - language (str): 编程语言(如"Python"/"C++")
            - status (str): 判题状态(枚举值:"Accepted", "WrongAnswer"等)
            - time_used (int): 耗时(毫秒)
            - memory_used (int): 内存使用(MB)
        示例结构:
            [{
                "submission_id": 1,
                "problem_id": 1,
                "submit_time": "Wed, 26 Feb 2025 08:00:00 GMT",
                "language": "Python",
                "status": "Accepted",
                "time_used": 500,
                "memory_used": 128
            }]
    """
    user = User(get_jwt())
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    if not contest.is_allowed_view(user):
        return jsonify({"error": f"user_id = {user.id} can't view contest(id = {contest_id})"}), 404

    submissions = Submission.query.filter_by(contest_id=contest_id).all()
    submission_list = []

    for submission in submissions:
        submission_data = {
            'submission_id': submission.id,
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

@app.route('/api/contest/get_contest_user_submission/<int:contest_id>', methods=['GET'])
@jwt_required()
def get_contest_user_submission(contest_id):
    """
    获取指定用户在比赛中的所有提交记录
    
    Args:
        contest_id (int): 路径参数,比赛唯一标识符
        (通过JWT Token获取用户身份)
    
    Returns:
        list[dict]: 提交记录列表,每个字典包含:
            - submission_id (int): 提交唯一标识符
            - problem_id (int): 题目唯一标识符
            - submit_time (str): 提交时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - language (str): 编程语言(如"Python"/"C++")
            - status (str): 判题状态(枚举值:"Accepted", "WrongAnswer"等)
            - time_used (int): 耗时(毫秒)
            - memory_used (int): 内存使用(MB)
        示例结构:
            [{
                "submission_id": 1,
                "problem_id": 1,
                "submit_time": "Wed, 26 Feb 2025 08:00:00 GMT",
                "language": "Python",
                "status": "Accepted",
                "time_used": 500,
                "memory_used": 128
            }]
    """
    user = User(get_jwt())
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    if not contest.is_allowed_view(user):
        return jsonify({"error": f"user_id = {user.id} can't view contest(id = {contest_id})"}), 404

    submissions = Submission.query.filter_by(contest_id=contest_id,user_id=user.id).all()
    submission_list = []

    for submission in submissions:
        submission_data = {
            'submission_id': submission.id,
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