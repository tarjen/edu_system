from flask import Flask, jsonify, request
from online_judge import app, jwt, jwt_required, get_jwt, db
from online_judge.models.homework import Homework, HomeworkStudent
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime
import json

@app.route('/api/homework/create', methods=['POST'])
@jwt_required()
def create_homework():
    """创建新作业
    
    Args:
        title (str): 作业标题
        start_time (str): 开始时间,RFC 1123格式(如:Wed, 26 Feb 2025 08:00:00 GMT)
        end_time (str): 结束时间,RFC 1123格式
        description (str, optional): 作业描述
        question_list (list[dict], optional): 初始题目列表 [{"question_id": int, "score": int}]
        student_ids (list[int], optional): 学生ID列表
        
    Returns:
        dict: 创建的作业信息
    """
    try:
        current_user = User(get_jwt())
        data = request.get_json()

        # 验证必填字段
        required_fields = ['title', 'start_time', 'end_time']
        if missing := [f for f in required_fields if f not in data]:
            return jsonify({"error": f"缺少必填字段: {missing}"}), 400

        # 解析RFC 1123时间格式
        try:
            start_time = parsedate_to_datetime(data['start_time'])
            end_time = parsedate_to_datetime(data['end_time'])
        except (TypeError, ValueError):
            return jsonify({"error": "时间格式应为RFC 1123 (如:Wed, 26 Feb 2025 08:00:00 GMT)"}), 400

        if end_time <= start_time:
            return jsonify({"error": "结束时间必须晚于开始时间"}), 400

        # 创建作业
        new_homework = Homework(
            title=data['title'].strip(),
            description=data.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            holder_id=current_user.id,
            holder_name=current_user.name,
        )

        db.session.add(new_homework)
        db.session.flush()  # 获取new_homework.id

        # 处理题目列表
        if question_list := data.get('question_list'):
            success, msg = new_homework.update_questions(question_list)
            if not success:
                db.session.rollback()
                return jsonify({"error": msg}), 400
        
        # 处理学生列表
        if student_ids := data.get('student_ids'):
            for student_id in student_ids:
                homework_student = HomeworkStudent(
                    homework_id=new_homework.id,
                    student_id=student_id
                )
                db.session.add(homework_student)

        db.session.commit()
        return jsonify({
            "success": True,
            "homework": new_homework.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500

@app.route('/api/homework/update/<int:homework_id>', methods=['POST'])
@jwt_required()
def update_homework(homework_id):
    """更新作业信息
    
    Args:
        homework_id (int): 作业ID
        title (str, optional): 新标题
        start_time (str, optional): 新开始时间
        end_time (str, optional): 新结束时间
        description (str, optional): 新描述
        question_list (list[dict], optional): 新题目列表 [{"question_id": int, "score": int}]
        student_ids (list[int], optional): 新的学生ID列表
        
    Returns:
        dict: 更新后的作业信息
    """
    current_user = User(get_jwt())
    homework = Homework.query.get(homework_id)
    
    if not homework:
        return jsonify({"error": "作业不存在"}), 404
    
    # 检查权限
    if homework.holder_id != current_user.id and current_user.power < 2:
        return jsonify({"error": "没有权限修改此作业"}), 403
        
    data = request.get_json()
    
    try:
        if 'title' in data:
            homework.title = data['title'].strip()
            
        if 'start_time' in data:
            homework.start_time = parsedate_to_datetime(data['start_time'])
            
        if 'end_time' in data:
            homework.end_time = parsedate_to_datetime(data['end_time'])
            
        if 'description' in data:
            homework.description = data['description']
            
        if 'question_list' in data:
            success, msg = homework.update_questions(data['question_list'])
            if not success:
                return jsonify({"error": msg}), 400
        
        # 处理学生列表更新
        if 'student_ids' in data:
            new_student_ids = set(data['student_ids'])
            
            # 获取当前的学生记录
            current_students = HomeworkStudent.query.filter_by(homework_id=homework_id).all()
            current_student_ids = {hs.student_id for hs in current_students}
            
            # 需要删除的学生
            students_to_remove = current_student_ids - new_student_ids
            if students_to_remove:
                HomeworkStudent.query.filter(
                    HomeworkStudent.homework_id == homework_id,
                    HomeworkStudent.student_id.in_(students_to_remove)
                ).delete(synchronize_session=False)
            
            # 需要添加的学生
            students_to_add = new_student_ids - current_student_ids
            for student_id in students_to_add:
                homework_student = HomeworkStudent(
                    homework_id=homework_id,
                    student_id=student_id
                )
                db.session.add(homework_student)
                
        db.session.commit()
        return jsonify({
            "success": True,
            "homework": homework.to_dict()
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500

@app.route('/api/homework/delete/<int:homework_id>', methods=['POST'])
@jwt_required()
def delete_homework(homework_id):
    """删除作业
    
    Args:
        homework_id (int): 作业ID
        
    Returns:
        dict: 操作结果
    """
    current_user = User(get_jwt())
    homework = Homework.query.get(homework_id)
    
    if not homework:
        return jsonify({"error": "作业不存在"}), 404
    
    # 检查权限
    if homework.holder_id != current_user.id and current_user.power < 2:
        return jsonify({"error": "没有权限删除此作业"}), 403
        
    try:
        success, msg = homework.delete()
        if not success:
            return jsonify({"error": msg}), 500
            
        return jsonify({"success": True, "message": "作业已删除"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500

@app.route('/api/homework/submit/<int:homework_id>', methods=['POST'])
@jwt_required()
def submit_homework(homework_id):
    """提交作业答案。

    学生提交作业的接口，包含以下限制：
    - 必须是作业的学生才能提交
    - 必须在作业时间范围内提交
    - 每份作业只能提交一次，提交后不能再次提交
    
    Args:
        homework_id (int): 作业ID
        answer_list (list): 答案列表 [{"question_id": int, "answer": str}, ...]
        
    Returns:
        JSON: {
            "success": bool,
            "score": int,      # 得分
            "submit_time": str  # GMT格式的提交时间
        }
        
    Raises:
        400: 参数错误、作业未开始、作业已结束、已提交过
        403: 无权限（不是作业学生）
        404: 作业不存在
    """
    current_user = User(get_jwt())
    homework = Homework.query.get(homework_id)
    
    if not homework:
        return jsonify({"error": "作业不存在"}), 404
        
    # 检查是否是作业的学生
    homework_student = HomeworkStudent.query.filter_by(
        homework_id=homework_id,
        student_id=current_user.id
    ).first()
    
    if not homework_student:
        return jsonify({"error": "您不是此作业的学生"}), 403
    
    # 检查是否已经提交过
    if homework_student.submit_time is not None:
        return jsonify({"error": "此作业您已提交过，不能重复提交"}), 400
    
    # 检查作业时间
    now = datetime.now()
    if now < homework.start_time:
        return jsonify({"error": "作业还未开始"}), 400
    if now > homework.end_time:
        return jsonify({"error": "作业已结束"}), 400
    
    data = request.get_json()
    if not data or 'answer_list' not in data:
        return jsonify({"error": "缺少answer_list"}), 400
    
    # 提交答案
    success, msg = homework_student.submit(data['answer_list'])
    print(f"success: {success}, msg: {msg}")
    if not success:
        return jsonify({"error": msg}), 400
        
    return jsonify({
        "success": True,
        "score": homework_student.score,
        "submit_time": format_datetime(homework_student.submit_time)
    }) 