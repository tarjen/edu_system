import os,yaml

from flask import Flask,jsonify,request,logging
from online_judge import app,db,jwt_required,get_jwt
from online_judge.api import User
from online_judge.models import Problem,Tag,ContestUser,Contest
@app.route('/api/problem/statement/get', methods=['GET'])
@jwt_required()
def get_problem_statement():
    """
    获取指定题目的详细信息说明
    
    通过 JSON 请求体传递必要参数，验证用户对于题目的访问权限后返回题目详细信息，
    需要满足以下条件之一：
    1. 比赛模式：题目归属于指定比赛，且用户在参赛名单中
    2. 练习模式：题目为公开状态，或用户是题目所有者且权限等级≥2

    Args:
        JSON Request Body:
            problem_id (int): 必填，要求查看的题目 ID
            contest_id (int): 可选的关联比赛 ID（默认值为 0表示非比赛模式）

    Returns:
        JSON Response:
            成功时返回 HTTP 200 和题目信息字典，包含：
                - id: 题目 ID
                - title: 题目标题
                - statement: 题目描述（Markdown 格式）
                - time_limit: 时间限制（毫秒）
                - memory_limit: 内存限制（MB）
                - 其他元数据...
            失败时返回对应的错误信息和状态码
    """
    user = User(get_jwt())
    data = request.get_json()

    # 从请求体中提取所需的数据  
    problem_id = data.get('problem_id')
    contest_id = data.get('contest_id')

    problem = Problem.query.filter_by(id=problem_id).first()

    if problem is None or (problem.is_public == False and contest_id == 0):
        return jsonify({"error": "problem is not available"}),404
    
    if contest_id != 0:
        contestuser = ContestUser.query.filter_by(contest_id=contest_id,user_id=user.id).first()
        if contestuser is None:
            return jsonify({"error": "the contest is not available for the user"}),404    
        if problem_id not in Contest.query.filter_by(id=contest_id).first().get_problems():
            return jsonify({"error": "the contest don't have this problem"}),404
    else:
        if not problem.is_public:
            if user.id != problem.user_id or user.power < 2:
                return jsonify({"error": "problem is not available for this user"}), 404
    problem_json = {}
    problem_json["id"] = problem_id
    problem_json["title"] = problem.title
    problem_json["writer"] = problem.user_name
    problem_json["time_limit"] = problem.time_limit
    problem_json["memory_limit"] = problem.memory_limit
    problem_json["tags"] = [tag.name for tag in problem.tags.all()]  # 替换get_tags_string()
    problem_json["accept_num"] = problem.accept_num
    problem_json["submit_num"] = problem.submit_num
    problem_json["is_public"] = problem.is_public
    problem_json["used_time"] = problem.used_time
    return jsonify(problem_json)

@app.route('/api/problem/statement/update/<int:problem_id>', methods=['POST'])
@jwt_required()
def update_problem_statement(problem_id):
    """
    上传指定题目的信息
    
    通过 JSON 请求体传递必要参数，验证用户对于题目的访问权限后返回题目详细信息

    Args:
        JSON Request Body:
            title (string): 题目名字
            time_limit (int): 题目时间限制
            memory_limit (int): 题目空间限制
            statement (string): 题目描述
            tags (list[int]): 题目标签

    Returns:

    """
    user = User(get_jwt())
    problem = Problem.query.filter_by(id=problem_id).first()
    if problem is None :
        return jsonify({"error": "problem is not available"}),404
    if problem.user_id != user.id:
        return jsonify({"error": "the user is not the owner of the problem"}),404
        
    problem_json = request.get_json()
    problem.title = problem_json["title"]
    problem.time_limit = problem_json["time_limit"]
    problem.memory_limit = problem_json["memory_limit"]
    problem.statement = problem_json["statement"]

        # 替换原有problem.tags字符串赋值逻辑
    tag_names = problem_json.get("tags", [])
    current_tags = {tag.name for tag in problem.tags.all()}
    new_tags = set(tag_names)

    # 删除不再关联的标签
    for tag in problem.tags.all():
        if tag.name not in new_tags:
            problem.tags.remove(tag)

    # 添加新关联的标签
    for name in new_tags - current_tags:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:  # 自动创建不存在的标签
            tag = Tag(name=name)
            db.session.add(tag)
        problem.tags.append(tag)
    
    problem.save()

    # update file 
    problem_path = os.join(os.getenv('PROBLEM_PATH'),str(problem_id))
    timelimit_file_path = os.path.join(problem_path, '.timelimit')
    with open(timelimit_file_path, 'w') as f:
        f.write(str(problem.time_limit))

    # 找到并修改problem.yaml文件
    yaml_file_path = os.path.join(problem_path, 'problem.yaml')
    with open(yaml_file_path, 'r') as f:
        data = yaml.safe_load(f)

    # 修改problem.yaml文件中limits:memory的值为ml
    data['limits']['memory'] = problem.memory_limit

    problem_statement_path = os.path.join(problem_path, "problem_statement")

    # 写入 problem.md
    with open(os.path.join(problem_statement_path, 'problem.md'), 'w', encoding='utf-8') as f:
        f.write(problem.statement)

    with open(yaml_file_path, 'w') as f:
        yaml.dump(data, f)
    return jsonify({"OK": f"update problem_id = {problem_id} ok"})    
    
@app.route('/api/problem/create', methods=['POST'])
@jwt_required()
def create_problem():
    """
    创建新题目
    
    Args:
        JSON Request Body:
            title (string): 题目标题（必填）
            time_limit (int): 时间限制 ms（必填）
            memory_limit (int): 内存限制 MB（必填）
            difficulty (int): 难度
            is_public (bool): 是否公开
            statement (string): 题目描述 Markdown（必填）
            tags (list[string]): 标签名称列表（默认空列表）
            
    Returns:
        成功：HTTP 201 和包含 problem_id 的JSON
        失败：对应错误状态码和描述
    """
    # 验证用户权限
    current_user = User(get_jwt())
    
    # 解析必填参数
    data = request.get_json()
    required_fields = ['title', 'time_limit', 'memory_limit', 'statement', 'difficulty', 'is_public']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "缺少必要参数"}), 404

    # 创建基础 Problem 记录
    new_problem = Problem(
        title=data['title'],
        time_limit=data['time_limit'],
        memory_limit=data['memory_limit'],
        statement=data['statement'],
        difficulty=data['difficulty'],
        user_id=current_user.id,
        user_name=current_user.name,
        is_public=data['is_public'],  
    )
    
    try:
        db.session.add(new_problem)
        db.session.commit()  # 先提交以获得 problem_id
        
        # 处理标签关联
        for tag_name in data.get('tags', []):
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            new_problem.tags.append(tag)
        db.session.commit()

        # 创建题目存储目录
        problem_path = os.path.join(
            os.getenv('PROBLEM_PATH'), 
            str(new_problem.id)
        )
        os.makedirs(problem_path, exist_ok=True)

        # 生成 timelimit 文件
        with open(os.path.join(problem_path, '.timelimit'), 'w') as f:
            f.write(str(new_problem.time_limit))

        # 生成 problem.yaml 文件
        yaml_data = {
            'limits': {
                'memory': new_problem.memory_limit,
                'output': "8MB"
            },
        }
        with open(os.path.join(problem_path, 'problem.yaml'), 'w') as f:
            yaml.safe_dump(yaml_data, f)

        # 创建题目标题描述目录
        problem_statement_path = os.path.join(problem_path, "problem_statement")
        os.makedirs(problem_statement_path, exist_ok=True)

        # 写入 problem.md
        with open(os.path.join(problem_statement_path, 'problem.md'), 'w', encoding='utf-8') as f:
            f.write(new_problem.statement)
        return jsonify({
            "OK": "create problem success",
            "problem_id": new_problem.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"create problem failed: {str(e)}")
        return jsonify({"error": f"create problem Failed {str(e)}"}), 500