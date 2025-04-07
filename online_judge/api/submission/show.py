from flask import Flask,jsonify,request
from online_judge import app,jwt_required,get_jwt
from online_judge.models import Submission,Contest,Problem
from online_judge.api import User

@app.route('/api/submission/filter', methods=['POST'])
@jwt_required()
def submission_filter():
    """根据多条件筛选提交记录
    
    支持通过组合多个查询参数过滤提交记录，返回分页后的结果集

    Args:
        user_id (int, optional): 筛选指定用户的提交记录
        problem_id (int, optional): 筛选指定题目的提交记录
        contest_id (int, optional): 筛选指定比赛的提交记录
        language (str, optional): 按编程语言过滤（枚举值：python/cpp）

    Returns:
        JSON: 包含分页信息的提交记录列表
        {
            "submissions": [
                {
                    "id": 123,
                    "problem_id": 456,
                    "user_id": 789,
                    "language": "python",
                    "submit_time": "2023-08-20T14:30:00",
                    "status": "Accepted",
                    "time_used": 100,    // 单位：毫秒
                    "memory_used": 2048  // 单位：KB
                },
                ...
            ],
            "pagination": {
                "total": 100,
                "current_page": 1,
                "per_page": 20
            }
        }

    Raises:
        400 Bad Request: 参数格式错误
        500 Internal Server Error: 数据库查询异常

    Notes:
        1. 当前版本未实现鉴权，后续需添加JWT验证
        2. 分页参数将在后续版本实现
    """
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

    return jsonify(submission_list),200

@app.route('/api/submission/get/<int:submission_id>', methods=['GET'])
@jwt_required()
def get_submission(submission_id):
    """获取指定提交记录的详细信息
    
    Args:
        submission_id (int): 路径参数，提交记录的唯一标识符

    Returns:
        JSON: 提交记录的完整信息
        {
            "id": 123,
            "code": "print('Hello World')",
            "language": "python",
            "user_id": 456,
            "problem_id": 789,
            "contest_id": 101,
            "submit_time": "2023-08-20T14:30:00",
            "status": "Accepted",
            "time_used": 100,      // 单位：毫秒
            "memory_used": 2048,   // 单位：KB
            "compile_error_info": ""  // 编译错误信息（如有）
        }

    Raises:
        404 Not Found: 指定ID的提交记录不存在

    Notes:
        1. 代码内容仅对提交者/管理员可见（待实现）
        2. 编译错误信息仅在状态为CompileError时返回
    """
    current_user = User(get_jwt())

    submission = Submission.query.get(submission_id)
    # 添加权限过滤
    if current_user.power < 2:  # 普通用户只能查自己
        if submission.user_id != current_user.id:
            return jsonify({"error": "user can't view this submission"}), 404

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
            "memory_used": submission.memory_used,
            "compile_error_info": submission.compile_error_info
        }
        return jsonify(submission_json),200