from datetime import datetime
from flask import request, jsonify
from online_judge import app, jwt_required, get_jwt
from online_judge.models.questions import Question, QuestionType
from online_judge.api import User
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/homework/generate', methods=['POST'])
@jwt_required()
def generate_homework():
    """作业生成接口，根据要求自动生成作业题目集合。
    
    从题库中选择符合要求的题目组合生成作业。需要教师权限。
    
    Args:
        Authorization (str): 请求头中的JWT令牌，格式：Bearer <token>
        
        JSON参数:
            title (str): 作业标题
            description (str, optional): 作业描述
            start_time (str): 开始时间,RFC 1123格式(如:Wed, 26 Feb 2025 08:00:00 GMT)
            end_time (str): 结束时间,RFC 1123格式
            total_score (int): 作业总分（默认100）
            question_count (int): 需要的题目数量
            difficulty_range (dict): 难度范围 {"min": 1, "max": 5}
            question_types (list[str]): 题目类型列表，可选值：["choice", "fill"]
            tags (list[str], optional): 题目标签列表
            student_ids (list[int], optional): 指定的学生ID列表
            
    Returns:
        JSON: 生成的作业信息，格式：
            {
                "success": bool,
                "homework": {
                    "id": int,
                    "title": str,
                    "description": str,
                    "start_time": str,
                    "end_time": str,
                    "questions": [{
                        "id": int,
                        "title": str,
                        "type": str,
                        "difficulty": int,
                        "score": int
                    }],
                    "total_score": int,
                    "student_count": int
                }
            }
            
    示例请求:
        POST /api/homework/generate
        Headers: { Authorization: Bearer <teacher_token> }
        Body: {
            "title": "第一次作业",
            "description": "这是第一次作业",
            "start_time": "Wed, 26 Feb 2025 08:00:00 GMT",
            "end_time": "Thu, 27 Feb 2025 08:00:00 GMT",
            "total_score": 100,
            "question_count": 5,
            "difficulty_range": {"min": 2, "max": 4},
            "question_types": ["choice", "fill"],
            "tags": ["Python", "基础"],
            "student_ids": [1001, 1002, 1003]
        }
    """
    try:
        current_user = User(get_jwt())
        
        # 检查权限（只有教师和管理员可以生成作业）
        if current_user.power < 1:
            return jsonify({"error": "没有权限生成作业"}), 403
            
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'start_time', 'end_time', 'question_count', 'difficulty_range', 'question_types']
        if missing := [f for f in required_fields if f not in data]:
            return jsonify({"error": f"缺少必填字段: {missing}"}), 400
            
        # 验证题目类型
        valid_types = [QuestionType.CHOICE.value, QuestionType.FILL.value]
        if not all(t in valid_types for t in data['question_types']):
            return jsonify({"error": "题目类型必须是'choice'或'fill'"}), 400
            
        # 验证难度范围
        diff_range = data['difficulty_range']
        if not (isinstance(diff_range, dict) and 
                'min' in diff_range and 'max' in diff_range and
                1 <= diff_range['min'] <= diff_range['max'] <= 5):
            return jsonify({"error": "难度范围必须在1-5之间"}), 400
            
        # TODO: 实现作业生成逻辑
        # 1. 根据条件筛选题目
        # 2. 按难度和类型分配分数
        # 3. 创建作业
        # 4. 分配给学生
        
        return jsonify({
            "error": "接口尚未实现"
        }), 501
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError as e:
        return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500