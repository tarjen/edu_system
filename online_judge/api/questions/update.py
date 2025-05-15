from flask import jsonify, request
from online_judge import app, jwt_required, get_jwt, db
from online_judge.models.questions import Question, QuestionType
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/questions/create', methods=['POST'])
@jwt_required()
def create_questions():
    """创建选择题或填空题
    
    Args:
        title (str): 题目标题
        content (str): 题目内容
        question_type (str): 题目类型('choice'或'fill')
        answer (str): 答案(选择题形如"AB"，填空题直接存答案)
        options (list[str], 仅选择题): 选项列表
        options_count (int, 仅选择题): 选项个数
        explanation (str, optional): 题目解析
        difficulty (int, optional): 难度(1-5,默认1)
        is_public (bool, optional): 是否公开(默认false)
        tags (list[str], optional): 标签列表
        
    Returns:
        dict: 创建的题目信息
    """
    try:
        current_user = User(get_jwt())
        data = request.get_json()
        print(f"Received data: {data}")  # 添加日志
        print(f"Current user: {current_user.__dict__}")  # 添加日志

        # 验证必填字段
        required_fields = ['title', 'content', 'question_type', 'answer']
        if missing := [f for f in required_fields if f not in data]:
            print(f"Missing fields: {missing}")  # 添加日志
            return jsonify({"error": f"缺少必填字段: {missing}"}), 400

        # 验证题目类型
        question_type = data['question_type']
        if question_type not in [QuestionType.CHOICE.value, QuestionType.FILL.value]:
            print(f"Invalid question type: {question_type}")  # 添加日志
            return jsonify({"error": "题目类型必须是'choice'或'fill'"}), 400

        # 选择题特殊验证
        if question_type == QuestionType.CHOICE.value:
            if 'options' not in data or 'options_count' not in data:
                print("Missing options or options_count")  # 添加日志
                return jsonify({"error": "选择题必须提供options和options_count"}), 400
            if not isinstance(data['options'], list):
                print(f"Options is not a list: {type(data['options'])}")  # 添加日志
                return jsonify({"error": "options必须是列表"}), 400
            if len(data['options']) != data['options_count']:
                print(f"Options length mismatch: {len(data['options'])} != {data['options_count']}")  # 添加日志
                return jsonify({"error": "options长度必须等于options_count"}), 400

        # 创建题目
        new_question = Question(
            title=data['title'].strip(),
            content=data['content'],
            user_id=current_user.id,
            user_name=current_user.name,
            question_type=question_type,
            answer=data['answer'],
            options=data.get('options'),
            options_count=data.get('options_count'),
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty', 1),
            is_public=data.get('is_public', False)
        )

        # 处理标签
        if tags := data.get('tags', []):
            from online_judge.models.problems import Tag
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                new_question.tags.append(tag)

        db.session.add(new_question)
        db.session.commit()

        return jsonify({
            "success": True,
            "question": {
                "id": new_question.id,
                "title": new_question.title,
                "content": new_question.content,
                "type": new_question.question_type,
                "options": new_question.get_options() if question_type == QuestionType.CHOICE.value else None,
                "options_count": new_question.options_count if question_type == QuestionType.CHOICE.value else None,
                "answer": new_question.answer,
                "explanation": new_question.explanation,
                "difficulty": new_question.difficulty,
                "is_public": new_question.is_public,
                "tags": [tag.name for tag in new_question.tags]
            }
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500 
        
@app.route('/api/questions/update/<int:question_id>', methods=['POST'])
@jwt_required()
def update_questions(question_id):
    """更新选择题或填空题
    
    Args:
        question_id (int): 题目ID
        title (str, optional): 新标题
        content (str, optional): 新内容
        options (list[str], optional): 新选项列表(仅选择题)
        answer (str, optional): 新答案
        explanation (str, optional): 新解析
        difficulty (int, optional): 新难度(1-5)
        is_public (bool, optional): 是否公开
        tags (list[str], optional): 新标签列表
        
    Returns:
        dict: 更新后的题目信息
    """
    try:
        current_user = User(get_jwt())
        question = Question.query.get(question_id)
        
        if not question:
            return jsonify({"error": "题目不存在"}), 404
            
        # 检查权限
        if question.user_id != current_user.id and current_user.power < 2:
            return jsonify({"error": "没有权限修改此题目"}), 403
            
        data = request.get_json()
        
        # 更新基本信息
        success, msg = question.update_problem(
            title=data.get('title'),
            content=data.get('content'),
            options=data.get('options'),
            answer=data.get('answer'),
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty'),
            is_public=data.get('is_public')
        )
        
        if not success:
            return jsonify({"error": msg}), 400
            
        # 更新标签
        if 'tags' in data:
            from online_judge.models.problems import Tag
            # 清除原有标签
            question.tags = []
            # 添加新标签
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                question.tags.append(tag)
                
        db.session.commit()
        
        return jsonify({
            "success": True,
            "question": {
                "id": question.id,
                "title": question.title,
                "content": question.content,
                "type": question.question_type,
                "options": question.get_options() if question.question_type == QuestionType.CHOICE.value else None,
                "options_count": question.options_count if question.question_type == QuestionType.CHOICE.value else None,
                "answer": question.answer,
                "explanation": question.explanation,
                "difficulty": question.difficulty,
                "is_public": question.is_public,
                "tags": [tag.name for tag in question.tags]
            }
        })
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500

@app.route('/api/questions/delete/<int:question_id>', methods=['POST'])
@jwt_required()
def delete_questions(question_id):
    """删除选择题或填空题
    
    Args:
        question_id (int): 题目ID
        
    Returns:
        dict: 操作结果
    """
    try:
        current_user = User(get_jwt())
        question = Question.query.get(question_id)
        
        if not question:
            return jsonify({"error": "题目不存在"}), 404
            
        # 检查权限
        if question.user_id != current_user.id and current_user.power < 2:
            return jsonify({"error": "没有权限删除此题目"}), 403
            
        # 删除题目
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "题目已删除"
        })
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500 