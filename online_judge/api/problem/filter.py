from datetime import datetime, timedelta
from flask import request, jsonify
from sqlalchemy import and_, or_, func,select
from sqlalchemy.orm import aliased
from online_judge import app,db
from online_judge.models import Problem, Contest, contest_problem, Tag, problem_tag

@app.route('/api/problem/filter', methods=['POST'])
def problem_filter():
    """
    题目筛选接口
    
    Args (JSON Body):
        title (str, optional): 题目名称模糊搜索
        tags (list[str], optional): 必须包含的标签列表
        min_difficulty (int, optional): 难度下限(与max_difficulty必须成对使用)
        max_difficulty (int, optional): 难度上限
        min_used (int, optional): 使用次数下限(与max_used必须成对使用)
        max_used (int, optional): 使用次数上限
        recent_unused (bool, optional): 是否排除半年内使用过的题目(默认false)

    Returns:
        JSON Response:
            list[int]: 符合条件的题目ID列表
    """
    data = request.get_json()
    
    # 参数提取
    title = data.get('title')
    tags = data.get('tags', [])
    min_d = data.get('min_difficulty')
    max_d = data.get('max_difficulty')
    min_u = data.get('min_used')
    max_u = data.get('max_used')
    recent_unused = data.get('recent_unused', False)

    # 参数验证
    if (min_d is None) != (max_d is None):
        return jsonify({"error": "Difficulty range requires both min and max"}), 404
    if (min_u is None) != (max_u is None):
        return jsonify({"error": "Usage range requires both min and max"}), 404

    # 构建基础查询
    query = Problem.query

    # 标题模糊搜索
    if title:
        query = query.filter(Problem.title.ilike(f'%{title}%'))

    # 难度范围过滤
    if min_d is not None and max_d is not None:
        query = query.filter(Problem.difficulty.between(min_d, max_d))

    # 使用次数过滤
    if min_u is not None and max_u is not None:
        query = query.filter(Problem.used_times.between(min_u, max_u))

    # 标签包含过滤
    if tags:
        # 验证标签存在性
        existing_tags = Tag.query.filter(Tag.name.in_(tags)).all()
        if len(existing_tags) != len(tags):
            existing_names = {t.name for t in existing_tags}
            missing = [t for t in tags if t not in existing_names]
            return jsonify({"error": f"Invalid tags: {missing}"}), 404

        # 构建多标签联合查询
        tag_subquery = db.session.query(
            problem_tag.c.problem_id
        ).join(Tag).filter(
            Tag.name.in_(tags)
        ).group_by(
            problem_tag.c.problem_id
        ).having(
            func.count() == len(tags)
        ).subquery()

        query = query.join(tag_subquery, Problem.id == tag_subquery.c.problem_id)

    # 排除近期使用
    if recent_unused:
        six_months_ago = datetime.now() - timedelta(days=180)
        
        recent_contests = select(Contest.id).where(
            Contest.start_time >= six_months_ago
        ).subquery()

        recent_problems_subquery = select(contest_problem.c.problem_id).join(
            recent_contests, contest_problem.c.contest_id == recent_contests.c.id
        ).distinct()

        query = query.filter(~Problem.id.in_(recent_problems_subquery))

    # 执行查询并返回结果
    try:
        problems = query.all()
        return jsonify([p.id for p in problems]), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 404