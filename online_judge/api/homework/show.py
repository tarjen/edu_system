from flask import Flask, jsonify, request
from online_judge import app, jwt, jwt_required, get_jwt, db
from online_judge.models.homework import Homework, HomeworkStudent, HomeworkQuestion
from online_judge.models.questions import Question
from online_judge.api import User
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime
import json

@app.route('/api/homework/filter', methods=['POST'])
@jwt_required()
def filter_homeworks():
    """根据POST请求中的JSON参数过滤作业
    
    Args:
        title (str, optional): 作业标题模糊搜索关键词
        holder_name (str, optional): 创建者名称
        
    Returns:
        list[dict]: 过滤后的作业列表
    """
    current_user = User(get_jwt())
    data = request.get_json()
    title_query = data.get('title')
    holder_query = data.get('holder_name')

    # 基础查询
    filtered_homeworks = Homework.query

    if title_query:
        filtered_homeworks = filtered_homeworks.filter(Homework.title.ilike(f'%{title_query}%'))
        
    if holder_query:
        filtered_homeworks = filtered_homeworks.filter(Homework.holder_name.ilike(f'%{holder_query}%'))

    return jsonify([homework.to_dict() for homework in filtered_homeworks.all()]), 200

@app.route('/api/homework/show/<int:homework_id>', methods=['GET'])
@jwt_required()
def get_homework(homework_id):
    """获取作业详细信息。

    根据用户角色返回不同级别的作业信息：
    - 管理员/创建者可以看到：
        * 作业基本信息（标题、描述、时间等）
        * 所有题目信息（包括答案和解释）
        * 所有学生的提交记录和得分
    - 参与的学生可以看到：
        * 作业基本信息
        * 题目信息（不包含答案和解释）
        * 自己的提交记录和得分
    - 其他用户：
        * 无权限查看

    Args:
        homework_id (int): 作业ID

    Returns:
        JSON: {
            'id': int,
            'title': str,
            'description': str,
            'start_time': str,  # GMT格式
            'end_time': str,    # GMT格式
            'holder_name': str,
            'questions': [{
                'id': int,
                'title': str,
                'content': str,
                'type': str,
                'score': int,
                'options': list,  # 仅选择题
                'answer': str,    # 仅管理员/创建者可见
                'explanation': str  # 仅管理员/创建者可见
            }],
            'students': [{  # 仅管理员/创建者可见
                'student_id': int,
                'score': int,
                'submit_time': str
            }],
            'student_record': {  # 仅学生本人可见
                'score': int,
                'submit_time': str,
                'answers': list
            }
        }

    Raises:
        404: 作业不存在
        403: 没有权限查看此作业
    """
    current_user = User(get_jwt())
    homework = Homework.query.get(homework_id)
    
    if not homework:
        return jsonify({"error": "作业不存在"}), 404
    
    # 权限检查
    if not (current_user.power >= 2 or  # 管理员
            homework.holder_id == current_user.id or  # 创建者
            HomeworkStudent.query.filter_by(  # 参与的学生
                homework_id=homework_id,
                student_id=current_user.id
            ).first()):
        return jsonify({"error": "没有权限查看此作业"}), 403
    
    response = homework.to_dict()
    # 获取题目详细信息
    questions = []
    homework_questions = HomeworkQuestion.query.filter_by(homework_id=homework_id).all()
    
    for hq in homework_questions:
        question = Question.query.get(hq.question_id)
        if question:
            # 基础题目信息（所有人可见）
            q_data = {
                'id': question.id,
                'title': question.title,
                'content': question.content,
                'type': question.question_type,
                'score': hq.score
            }
            
            # 选择题额外信息
            if question.question_type == 'choice':
                q_data['options'] = question.get_options()
                q_data['options_count'] = question.options_count
            
            # 判断是否有权限查看答案和解释
            can_view_answer = (current_user.power >= 2 or 
                             homework.holder_id == current_user.id or 
                             question.user_id == current_user.id)
            
            if can_view_answer:
                q_data['answer'] = question.answer
                q_data['explanation'] = question.explanation
            
            questions.append(q_data)
    
    # 获取当前用户的提交记录（如果是学生）
    student_record = None
    if current_user.power < 2 and homework.holder_id != current_user.id:
        student_record = HomeworkStudent.query.filter_by(
            homework_id=homework_id,
            student_id=current_user.id
        ).first()


    response['questions'] = questions
    
    # 如果是创建者或管理员，添加学生列表
    if current_user.power >= 2 or homework.holder_id == current_user.id:
        students = HomeworkStudent.query.filter_by(homework_id=homework_id).all()
        response['students'] = [{
            'student_id': hs.student_id,
            'score': hs.score,
            'submit_time': format_datetime(hs.submit_time) if hs.submit_time else None,
        } for hs in students]
    # 如果是学生，添加其提交记录
    elif student_record:
        response['student_record'] = {
            'score': student_record.score,
            'submit_time': format_datetime(student_record.submit_time) if student_record.submit_time else None,
            'answers': student_record.get_answer() if student_record.answer else []
        }
    
    return jsonify(response) 