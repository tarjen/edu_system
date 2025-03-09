import os,json
import httpx
from volcenginesdkarkruntime import Ark
from typing import Dict, List, Union

def call_ai_api(
    messages: List[Dict[str, str]],
    model: str = "deepseek-r1-250120",
    stream: bool = False
) -> Dict[str, Union[str, Dict]]:
    """
    调用火山引擎AI模型的API
    
    :param messages: 消息列表，格式 [{"role": "user", "content": "你的问题"}]
    :param model: 使用的模型名称（默认deepseek-r1-250120）
    :param stream: 是否使用流式传输（默认False）
    :return: 结构化响应，包含content/reasoning_content或错误信息
    """
    try:
        # 初始化客户端（推荐从环境变量读取认证信息）
        client = Ark(
            api_key=os.getenv("ARK_API_KEY"),
            # 或使用ak/sk方式:
            # ak=os.getenv("VOLC_ACCESSKEY"),
            # sk=os.getenv("VOLC_SECRETKEY"),
            timeout=httpx.Timeout(1800)
        )
        
        # 发起请求
        if stream:
            response_stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            # 处理流式响应
            full_content = ""
            for chunk in response_stream:
                if chunk.choices:
                    content = chunk.choices[0].delta.reasoning_content or chunk.choices[0].delta.content
                    if content:
                        full_content += content
            return {"content": full_content}
        else:
            # 处理标准响应
            completion = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return {
                "content": completion.choices[0].message.content,
                "reasoning_content": completion.choices[0].message.reasoning_content
            }
            
    except Exception as e:
        return {"error": str(e)}


from datetime import datetime, timedelta
from typing import List, Dict, Union
from flask import request, jsonify
from sqlalchemy import select
from online_judge import db,app,jwt_required,get_jwt
from online_judge.api import User
from online_judge.models import Problem, Contest, contest_problem, Tag, problem_tag
from sqlalchemy import func  

@app.route('/api/contest/select_problems', methods=['POST'])
@jwt_required()
def select_problems():
    """智能选题接口，根据比赛要求筛选并返回题目集合。
    
    使用AI模型从候选题库中选择符合比赛参数要求的题目组合。需要管理员权限。
    
    Args:
        Authorization (str): 请求头中的JWT令牌，格式：Bearer <token>
        
        JSON参数:
            average_difficulty (float): 要求的平均难度（1-5）
            problem_count (int): 需要选择的题目数量
            average_accept_rate (float): 目标平均通过率（0-1）
            average_used_times (int): 允许的平均使用次数
            allow_recent_used (bool): 是否允许使用近6个月用过的题目
            allowed_types (list[str]): 允许的题目类型标签列表
            
    Returns:
        JSON: 包含选中题目ID列表的响应，格式：
            {
                "selected_problems": [int]
            }
            
    示例请求:
        POST /api/contest/select_problems
        Headers: { Authorization: Bearer <admin_token> }
        Body: {
            "average_difficulty": 3,
            "problem_count": 5,
            "average_accept_rate": 0.6,
            "average_used_times": 2,
            "allow_recent_used": false,
            "allowed_types": ["算法", "图论"]
        }
    """
    try:
        # 权限验证
        current_user = User(get_jwt())
        if current_user.power < 2:
            return jsonify({"error": "Insufficient privileges"}), 404

        # 参数验证
        data = request.get_json()
        required_fields = [
            'average_difficulty', 'problem_count',
            'average_accept_rate', 'average_used_times',
            'allow_recent_used', 'allowed_types'
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required parameters"}), 404

        # 题目初步筛选
        base_query = Problem.query
        
        # 排除最近6个月使用的题目
        if not data['allow_recent_used']:
            six_months_ago = datetime.time() - timedelta(days=180)
            recent_contests = select(Contest.id).where(
                Contest.start_time >= six_months_ago
            ).subquery()
            recent_problems = select(contest_problem.c.problem_id).join(
                recent_contests, contest_problem.c.contest_id == recent_contests.c.id
            ).distinct()
            base_query = base_query.filter(~Problem.id.in_(recent_problems))

        # 标签筛选
        if data['allowed_types']:
        # 获取包含任一指定标签的题目ID
            tag_subquery = (
                select(problem_tag.c.problem_id)
                .join(Tag)
                .where(Tag.name.in_(data['allowed_types']))
                .distinct()  # 去重避免重复ID
            )
            # 应用筛选条件
            base_query = base_query.filter(Problem.id.in_(tag_subquery))

        # 获取候选题目
        candidate_problems = base_query.all()
        if not candidate_problems:
            return jsonify({"error": "No available problems match criteria"}), 404

        # 构造AI请求数据
        problem_list = [{
            "题目编号": p.id,
            "难度": p.difficulty,
            "通过率": round(p.accept_num / p.submit_num, 2) if p.submit_num > 0 else 0.0,
            "使用次数": p.used_times,
            "题目类型": [t.name for t in p.tags]
        } for p in candidate_problems]

        request_data = {
            "比赛要求": {
                "平均难度": data['average_difficulty'],
                "题目数量": data['problem_count'],
                "平均通过率": data['average_accept_rate'],
                "平均使用次数": data['average_used_times'],
                "允许的题目类型": data['allowed_types']
            },
            "候选题目": problem_list
        }

        # 调用AI模型
        messages = [{
            "role": "user",
            "content": f"我需要你帮我出一场比赛,返回时只需要返回一个包含题目编号的list，用','分隔（例如 [4,5,6,7,8] 不要有任何多余的字符回车），要求如下：\n{json.dumps(request_data, ensure_ascii=False)}"
        }]
        ai_response = call_ai_api(messages)
        if "error" in ai_response:
            return jsonify({"error": f"AI service error: {ai_response['error']}"}), 404
        # print(f"messages = {messages}")
        # print(f"ai_respoinse = {ai_response}")
        # 解析AI响应
        try:
            selected_ids = json.loads(ai_response['content'])
            if not isinstance(selected_ids, list):
                raise ValueError
        except Exception as e:
            return jsonify({"error": "Invalid AI response format"}), 404

        # 验证题目ID有效性
        valid_ids = {p.id for p in candidate_problems}
        valid_selection = [pid for pid in selected_ids if pid in valid_ids]
        
        return jsonify({"selected_problems": valid_selection}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"System error: {str(e)}"}), 404