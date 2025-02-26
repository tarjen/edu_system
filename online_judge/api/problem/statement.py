import os


from flask import Flask,jsonify,request
from online_judge import app,db
from online_judge.models.problems import Problem,Tag
@app.route('/api/problem/statement/get', methods=['GET'])
def get_problem_statement(problem_id):
    #TODO JWT_CHECK and check if the user allowed to use the problem

    problem = Problem.query.filter_by(id=problem_id).first()
    if problem is None:
        return jsonify({"error": "Problem not found"}), 404    
    else:
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
def update_problem_statement(problem_id):
    #TODO JWT_CHECK and check if the user allowed to edit the problem

    problem_json = request.get_json()
    problem = Problem.query.filter_by(id=problem_id).first()
    problem.title = problem_json["title"]
    problem.user_name = problem_json["writer"]
    problem.time_limit = problem_json["time_limit"]
    problem.memory_limit = problem_json["memory_limit"]
    problem.accept_num = problem_json["accept_num"]
    problem.submit_num = problem_json["submit_num"]
    problem.is_public = problem_json["is_public"]

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
    PATH = os.getenv('PROBLEM_PATH')
    timelimit_file_path = os.path.join(PATH, str(problem_id), '.timelimit')
    with open(timelimit_file_path, 'w') as f:
        f.write(str(problem.time_limit))

    # 找到并修改problem.yaml文件
    yaml_file_path = os.path.join(PATH, str(problem_id), 'problem.yaml')
    with open(yaml_file_path, 'r') as f:
        data = yaml.safe_load(f)

    # 修改problem.yaml文件中limits:memory的值为ml
    data['limits']['memory'] = problem.memory_limit

    with open(yaml_file_path, 'w') as f:
        yaml.dump(data, f)
    return jsonify({"OK": f"update problem_id = {problem_id} ok"})    
    
