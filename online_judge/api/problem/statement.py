from flask import Flask,jsonify
from online_judge import app
from online_judge.models.problems import Problem
@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem = Problem.query.filter_by(problem_id=problem_id).first()
    if problem is None:
        return jsonify({"error": "Problem not found"}), 404    
    else:
        problem_json = {}
        problem_json["id"] = problem_id
        problem_json["title"] = problem.title
        problem_json["writer"] = problem.user_name
        problem_json["time_limit"] = problem.time_limit
        problem_json["memory_limit"] = problem.memory_limit
        problem_json["tags"] = problem.get_tags_string()
        problem_json["accept_num"] = problem.accept_num
        problem_json["submit_num"] = problem.submit_num
        problem_json["is_public"] = problem.is_public
        return jsonify(problem_json)
