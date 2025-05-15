from flask import jsonify, request
from online_judge import app, jwt_required, get_jwt, db
from online_judge.models.questions import Question, QuestionType
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/questions/filter', methods=['POST'])
@jwt_required()
def filter_questions():
    """筛选选择题或填空题
    
    Args:
        title (str, optional): 题目标题模糊搜索
        type (str, optional): 题目类型('choice'或'fill')
        tags (list[str], optional): 必须包含的标签列表
        min_difficulty (int, optional): 难度下限(与max_difficulty必须成对使用)
        max_difficulty (int, optional): 难度上限
        min_used (int, optional): 使用次数下限(与max_used必须成对使用)
        max_used (int, optional): 使用次数上限
        creator_name (str, optional): 创建者名称
        
    Returns:
        list[dict]: 符合条件的题目列表
    """
    try:
        current_user = User(get_jwt())
        data = request.get_json()
        
        # 构建基础查询
        query = Question.query
        
        # 标题模糊搜索
        if title := data.get('title'):
            query = query.filter(Question.title.ilike(f'%{title}%'))
            
        # 题目类型过滤
        if question_type := data.get('type'):
            if question_type not in [QuestionType.CHOICE.value, QuestionType.FILL.value]:
                return jsonify({"error": "题目类型必须是'choice'或'fill'"}), 400
            query = query.filter(Question.question_type == question_type)
            
        # 标签过滤
        if tags := data.get('tags'):
            from online_judge.models.problems import Tag
            for tag_name in tags:
                tag_query = Tag.query.filter_by(name=tag_name).first()
                if tag_query:
                    query = query.filter(Question.tags.contains(tag_query))
                    
        # 难度范围过滤
        min_d = data.get('min_difficulty')
        max_d = data.get('max_difficulty')
        if (min_d is None) != (max_d is None):
            return jsonify({"error": "难度范围需要同时提供上下限"}), 400
        if min_d is not None and max_d is not None:
            query = query.filter(Question.difficulty.between(min_d, max_d))
            
        # 使用次数范围过滤
        min_u = data.get('min_used')
        max_u = data.get('max_used')
        if (min_u is None) != (max_u is None):
            return jsonify({"error": "使用次数范围需要同时提供上下限"}), 400
        if min_u is not None and max_u is not None:
            query = query.filter(Question.used_times.between(min_u, max_u))
            
        # 创建者名称过滤
        if creator_name := data.get('creator_name'):
            query = query.filter(Question.user_name == creator_name)
            
        # 权限过滤
        if current_user.power < 2:  # 非管理员
            query = query.filter(
                (Question.is_public == True) |  # 公开题目
                (Question.user_id == current_user.id)  # 自己创建的题目
            )
            
        # 执行查询
        questions = query.all()
        
        # 构造返回数据
        result = []
        for q in questions:
            question_data = {
                "id": q.id,
                "title": q.title,
                "type": q.question_type,
                "difficulty": q.difficulty,
                "is_public": q.is_public,
                "user_name": q.user_name,
                "accept_num": q.accept_num,
                "submit_num": q.submit_num,
                "accuracy_rate": q.accuracy_rate,
                "used_times": q.used_times,
                "tags": [tag.name for tag in q.tags]
            }
            
            # 选择题额外信息
            if q.question_type == QuestionType.CHOICE.value:
                question_data.update({
                    "options_count": q.options_count
                })
                
            result.append(question_data)
            
        return jsonify(result)
        
    except SQLAlchemyError as e:
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500 