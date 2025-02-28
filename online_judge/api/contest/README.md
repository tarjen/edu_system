这个Flask API包含用于管理在线评测系统中比赛的端点。

1. 根据POST请求中的JSON参数过滤比赛:
    - 路由: /api/contest/filter
    - 方法: POST
    - 描述: 根据请求体中的JSON参数过滤比赛。
    - 参数:
        - (通过JSON Body传递参数)
        - title (str, 可选): 比赛标题模糊搜索关键词,支持部分匹配。
        - holder_name (str, 可选): 主办方名称精确匹配(区分大小写)。
    - 返回:
        - list[dict]: 过滤后的比赛数据列表,每个字典包含:
            - contest_id (int): 比赛唯一标识符
            - contest_title (str): 比赛标题
            - holder_id (int): 主办用户ID
            - holder_name (str): 主办用户名称
            - start_time (str): 比赛开始时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - end_time (str): 比赛结束时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - information (str): 比赛描述信息

2. 根据GET请求中的 contest_id(int) 获得比赛具体信息:
    - 路由: /api/contest/getinfo/<int:contest_id>
    - 方法: GET
    - 描述: 根据比赛ID获取特定比赛信息。
    - 参数:
        - contest_id(int): 比赛编号
    - 返回:
        - dict: 比赛信息,包含比赛id、比赛标题、管理人id、管理人名字、起始时间、结束时间、比赛信息、题目编号、排行榜
        - TODO: 加一个ranklist例子

3. 获取指定比赛中用户已解决的题目列表:
    - 路由: /api/contest/get_contest_user_solved_problem/<int:contest_id>
    - 方法: POST
    - 描述: 获取指定比赛中用户已解决的题目列表。
    - 参数:
        - contest_id (int): 路径参数,比赛唯一标识符
        - (通过JWT Token获取用户身份)
    - 返回:
        - list[int]: 用户已解决的题目ID列表,格式示例: [103, 105, 107]
        - 数据结构说明:
            - 每个元素为题目唯一标识符(整数)
            - 按实际解决顺序排序

4. 获取指定比赛的所有参赛用户:
    - 路由: /api/contest/get_all_user/<int:contest_id>
    - 方法: GET
    - 描述: 获取特定比赛的所有参赛用户。
    - 参数:
        - contest_id (int): 路径参数,比赛唯一标识符
    - 返回:
        - list[int]: 参赛用户ID列表,格式示例: [1001, 1003, 1005]
        - 数据结构说明:
            - 每个元素为用户唯一标识符(整数)
            - 列表按用户加入比赛的时间排序

5. 获取比赛中的所有提交记录:
    - 路由: /api/contest/get_all_submission/<int:contest_id>
    - 方法: GET
    - 描述: 获取特定比赛中的所有提交记录。
    - 参数:
        - contest_id (int): 路径参数,比赛唯一标识符
        - (通过JWT Token获取用户身份)
    - 返回:
        - list[dict]: 提交记录列表,每个字典包含:
            - problem_id (int): 题目唯一标识符
            - submit_time (str): 提交时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - language (str): 编程语言(如"Python"/"C++")
            - status (str): 判题状态(枚举值:"Accepted", "WrongAnswer"等)
            - time_used (int): 耗时(毫秒)
            - memory_used (int): 内存使用(MB)
        - 示例结构:
            [{
                "problem_id": 103,
                "submit_time": "Wed, 26 Feb 2025 08:00:00 GMT",
                "language": "Python",
                "status": "Accepted",
                "time_used": 500,
                "memory_used": 128
            }]

6. 获取指定用户在比赛中的所有提交记录:
    - 路由: /api/contest/get_contest_user_submission/<int:contest_id>
    - 方法: GET
    - 描述: 获取特定比赛中指定用户的所有提交记录。
    - 参数:
        - contest_id (int): 路径参数,比赛唯一标识符
        - (通过JWT Token获取用户身份)
    - 返回:
        - list[dict]: 提交记录列表,每个字典包含:
            - problem_id (int): 题目唯一标识符
            - submit_time (str): 提交时间(Wed, 26 Feb 2025 08:00:00 GMT)
            - language (str): 编程语言(如"Python"/"C++")
            - status (str): 判题状态(枚举值:"Accepted", "WrongAnswer"等)
            - time_used (int): 耗时(毫秒)
            - memory_used (int): 内存使用(MB)
        - 示例结构:
            [{
                "problem_id": 103,
                "submit_time": "Wed, 26 Feb 2025 08:00:00 GMT",
                "language": "Python",
                "status": "Accepted",
                "time_used": 500,
                "memory_used": 128
            }]

7. 更新比赛基础信息接口:
    - 路由: /api/contest/update_contest_info/<int:contest_id>
    - 方法: POST
    - 描述: 更新比赛基础信息。
    - 参数:
        - contest_id (int): 路径参数,比赛唯一标识符
        - (通过JWT Token获取用户身份)
    - 返回:
        - 更新成功消息

8. 全量更新比赛的关联用户列表:
    - 路由: /api/contest/update_contest_user/<int:contest_id>
    - 方法: POST
    - 描述: 使用新用户ID替换当前比赛参与者列表,执行原子添加/删除操作。
    - 参数:
        - contest_id (int): 路径参数,目标比赛的唯一标识符
        - users (list[int], 可选): 请求体JSON中的用户ID列表。示例: [1001, 1003, 1005]
    - 返回:
        - JSON响应包含操作结果

9. 全量更新比赛关联的题目列表:
    - 路由: /api/contest/<int:contest_id>/problems
    - 方法: POST
    - 描述: 使用题目ID列表替换当前比赛关联的题目,执行原子更新操作。
    - 参数:
        - contest_id (int): 路径参数,目标比赛的唯一标识符
        - problem_ids (list[int]): 请求体JSON中的题目ID列表。示例: [45, 67, 89]
    - 返回:
        - JSON响应
10. 创建新的比赛:
    - 路由: /api/contests
    - 方法: POST
    - 描述: 通过JSON请求体接收比赛信息,创建新比赛并返回创建结果。
    - 参数:
        - (通过JSON Body传递参数)
        - title (str): 比赛标题,必填,长度1-80字符
        - start_time (str): 开始时间,RFC 1123格式字符串(如:Wed, 26 Feb 2025 08:00:00 GMT)
        - end_time (str): 结束时间,RFC 1123格式字符串
        - information (str, optional): 比赛描述信息,最大长度500字符
        - problem_ids (list[int], optional): 初始关联题目ID列表
    - 返回
        - JSON响应