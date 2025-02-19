from flask import Flask,jsonify
from online_judge import app

@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    if problem_id in problems:
        return jsonify(problems[problem_id])
    else:
        return jsonify({"error": "Problem not found"}), 404