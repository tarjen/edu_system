from flask import jsonify, request
from online_judge import app, jwt_required, get_jwt, db
from online_judge.models.questions import Question, QuestionType
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/questions/get/<int:question_id>', methods=['GET'])
@jwt_required()
def get_questions(question_id):
    """获取选择题或填空题的详细信息。

    根据用户角色返回不同级别的题目信息：
    - 管理员/题目作者可以看到：
        * 题目的所有基本信息
        * 答案和解析
        * 统计数据（提交数、正确率等）
    - 普通用户可以看到：
        * 公开题目的基本信息（不含答案和解析）
        * 统计数据
    - 未授权用户：
        * 无权限查看非公开题目

    Args:
        question_id (int): 题目ID

    Returns:
        JSON: {
            'id': int,
            'title': str,
            'content': str,
            'type': str,          # 题目类型：'choice' 或 'fill'
            'difficulty': int,     # 难度等级：1-5
            'is_public': bool,     # 是否公开
            'user_id': int,        # 创建者ID
            'user_name': str,      # 创建者用户名
            'accept_num': int,     # 通过次数
            'submit_num': int,     # 提交次数
            'accuracy_rate': float,# 正确率
            'tags': list[str],     # 题目标签列表
            'options': list[str],  # 仅选择题：选项列表
            'options_count': int,  # 仅选择题：选项数量
            'answer': str,         # 仅管理员/作者可见
            'explanation': str     # 仅管理员/作者可见
        }

    Raises:
        404: 题目不存在
        403: 无权限查看此题目
        500: 数据库操作失败
    """
    try:
        current_user = User(get_jwt())
        question = Question.query.get(question_id)
        
        if not question:
            return jsonify({"error": "题目不存在"}), 404
            
        # 检查访问权限
        if not question.is_public and question.user_id != current_user.id and current_user.power < 2:
            return jsonify({"error": "没有权限查看此题目"}), 403
            
        # 判断是否有权限查看答案和解析
        can_view_answer = (current_user.power >= 2 or 
                         question.user_id == current_user.id)
        
        response = {
            "id": question.id,
            "title": question.title,
            "content": question.content,
            "type": question.question_type,
            "difficulty": question.difficulty,
            "is_public": question.is_public,
            "user_id": question.user_id,
            "user_name": question.user_name,
            "accept_num": question.accept_num,
            "submit_num": question.submit_num,
            "accuracy_rate": question.accuracy_rate,
            "tags": [tag.name for tag in question.tags]
        }
        
        # 选择题额外信息
        if question.question_type == QuestionType.CHOICE.value:
            response.update({
                "options": question.get_options(),
                "options_count": question.options_count
            })
            
        # 答案和解析(仅管理员和题目作者可见)
        if can_view_answer:
            response.update({
                "answer": question.answer,
                "explanation": question.explanation
            })
            
        return jsonify(response)
        
    except SQLAlchemyError as e:
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500 