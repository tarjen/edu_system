from flask import Flask,jsonify,request
from online_judge import app,jwt,jwt_required,get_jwt,db
from online_judge.models.problems import Problem
from online_judge.models.contests import Contest,ContestUser
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError
import json

@app.route('/api/contest/update_contest_info/<int:contest_id>', methods=['POST'])
@jwt_required()
def update_contest_info(contest_id):
    """
    更新比赛基础信息接口

    JWT验证:
    - 需要在请求头携带有效JWT Token
    - Token中必须包含用户权限信息

    访问权限:
    - 比赛创建者(holder_id与用户ID匹配)
    - 管理员用户(用户权限power >=2)

    Args:
        contest_id (int): 路径参数,比赛唯一标识符
        (通过JWT Token获取用户身份)
    Returns:
    """
    user = User(get_jwt())
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    if not contest.is_allowed_edit(user):
        return jsonify({"error": f"user_id = {user.id} can't update contest(id = {contest_id})"}) 

    data = request.get_json()
    if 'title' in data:
        contest.title = data['title']
    if 'information' in data:
        contest.information = data['information']
    contest.save()
    return jsonify({"OK": "update success"})

@app.route('/api/contest/update_contest_user/<int:contest_id>', methods=['POST'])
@jwt_required()
def update_contest_user(contest_id):
    """
    全量更新比赛的关联用户列表
    
    用请求中提供的用户ID列表替换当前比赛所有关联用户,执行原子化的添加/删除操作。
    要求有效的JWT认证且用户具备管理员权限。

    Args:
        contest_id (int): 路径参数,目标比赛的唯一标识符
        users (list[int], optional): 请求体JSON中的用户ID列表。示例: [1001, 1003, 1005]

    Returns:
        JSON响应:
        - 成功 (200):
            {
                "success": True,
                "added": [1005, 1006],  # 本次新增的用户ID
                "removed": [1002],       # 本次移除的用户ID
                "total": 3               # 更新后的用户总数
            }
    """
    try:
        user = User(get_jwt())
        contest = Contest.query.filter_by(id=contest_id).first()    
        if contest is None:
            return jsonify({"error": "contest not found"}), 404    
        if not contest.is_allowed_edit(user):
            return jsonify({"error": f"user_id = {user.id} can't update contest(id = {contest_id})"}) 
        data = request.get_json()

        # 验证和处理用户ID列表
        new_users_list = data.get('users', [])  # 直接获取列表
        try:
            # 转换为整数并去重
            new_users = list({int(uid) for uid in new_users_list})
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user ID format, expected integer list"}), 400

        # 获取当前关联用户
        current_users = contest.get_current_users()  # 需要实现该方法

        # 计算需要操作的ID
        users_to_add = list(set(new_users) - set(current_users))
        users_to_remove = list(set(current_users) - set(new_users))

        # 执行数据库操作
        try:
            if users_to_remove:
                contest.delete_users(users_to_remove)
            
            if users_to_add:
                contest.add_users(users_to_add)
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": "Failed to edit database"}), 500

        return jsonify({
            "success": True,
            "added": users_to_add,
            "removed": users_to_remove,
            "total": len(new_users)
        }), 200
    except Exception as e:
        # 全局异常捕获
        return jsonify({"error": str(e)}), 500

@app.route('/api/contest/update_problems/<int:contest_id>', methods=['POST'])
@jwt_required()
def update_contest_problems(contest_id):
    """全量更新比赛关联的题目列表
    
    用请求中的题目ID列表替换当前比赛所有关联题目,执行原子化更新操作。
    要求有效的JWT且用户。
    - 用户需满足以下任一条件:
        1. 比赛创建者 (contest.holder_id == user.id)
        2. 管理员用户 (user.power >= 2)

    Args:
        contest_id (int): 路径参数,目标比赛的唯一标识符
        problem_ids (list[int]): 请求体JSON中的题目ID列表。示例: [45, 67, 89]

    Returns:
        JSON响应
    """
    user = User(get_jwt())
    contest = Contest.query.filter_by(id=contest_id).first()    
    if contest is None:
        return jsonify({"error": "contest not found"}), 404    
    if not contest.is_allowed_edit(user):
        return jsonify({"error": f"user_id = {user.id} can't update contest(id = {contest_id})"}) 

    data = request.get_json()
    if not data or 'problem_ids' not in data:
        return jsonify({"error": "Missing problem_ids"}), 400

    try:
        problem_ids = list(map(int, data['problem_ids']))
        contest.update_problems(problem_ids, user)
        return jsonify({
            "success": True,
            "problem_ids": contest.get_problems()
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    
from email.utils import parsedate_to_datetime, format_datetime
from datetime import datetime

@app.route('/api/contests', methods=['POST'])
@jwt_required()
def create_contest():
    """创建新的比赛
    
    通过JSON请求体接收比赛信息,创建新比赛并返回创建结果。
    要求有效的JWT认证。

    Args:
        (通过JSON Body传递参数)
        title (str): 比赛标题,必填,长度1-80字符
        start_time (str): 开始时间,RFC 1123格式字符串(如:Wed, 26 Feb 2025 08:00:00 GMT)
        end_time (str): 结束时间,RFC 1123格式字符串
        information (str, optional): 比赛描述信息,最大长度500字符
        problem_ids (list[int], optional): 初始关联题目ID列表

    Returns:
        JSON响应
        
    """
    try:
        # 获取当前用户并验证权限
        current_user = User(get_jwt())

        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400

        # 验证必填字段
        required_fields = ['title', 'start_time', 'end_time']
        if missing := [f for f in required_fields if f not in data]:
            return jsonify({"error": f"缺少必填字段: {missing}"}), 400

        # 解析 RFC 1123 时间格式
        try:
            start_time = parsedate_to_datetime(data['start_time'])
            end_time = parsedate_to_datetime(data['end_time'])
        except (TypeError, ValueError):
            return jsonify({"error": "时间格式应为 RFC 1123 (如:Wed, 26 Feb 2025 08:00:00 GMT)"}), 400

        # 验证时间逻辑
        if end_time <= start_time:
            return jsonify({"error": "结束时间必须晚于开始时间"}), 400

        # 创建比赛实例
        new_contest = Contest(
            title=data['title'].strip(),
            start_time=start_time,
            end_time=end_time,
            holder_id=current_user.id,
            holder_name=current_user.name,
            information=data.get('information', '')[:500]
        )

        # 处理初始题目关联(需要已实现的权限验证)
        if problem_ids := data.get('problem_ids'):
            valid_problems = Problem.query.filter(
                (Problem.is_public == True) |
                (Problem.user_id == current_user.id) |
                (current_user.power >= 2)
            ).filter(Problem.id.in_(problem_ids)).all()
            
            if len(valid_problems) != len(problem_ids):
                invalid_ids = set(problem_ids) - {p.id for p in valid_problems}
                return jsonify({"error": f"无权添加题目: {invalid_ids}"}), 403

            new_contest.problems = valid_problems

        db.session.add(new_contest)
        db.session.commit()

        # 格式化返回时间
        return jsonify({
            "success": True,
            "contest": {
                "id": new_contest.id,
                "title": new_contest.title,
                "holder_id": new_contest.holder_id,
                "start_time": format_datetime(new_contest.start_time),
                "end_time": format_datetime(new_contest.end_time),
                "problem_ids": [p.id for p in new_contest.problems]
            }
        }), 201

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "数据库操作失败"}), 500
