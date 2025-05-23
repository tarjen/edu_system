# API 文档

## `/api/data` (GET)
*文件位置*: `online_judge/__init__.py`


---

## `/protected` (GET)
*文件位置*: `online_judge/__init__.py`


---

## `/api/contest/select_problems` (POST)
*文件位置*: `online_judge/api/contest/gen_contest.py`

**描述**: 题目选择接口，根据比赛要求筛选并返回题目集合。

从候选题库中选择符合比赛参数要求的题目组合。需要管理员权限。

### 参数说明
- `Authorization` (str): 请求头中的JWT令牌，格式：Bearer <token>
- JSON参数:
- `average_difficulty` (float): 要求的平均难度（1-5）
- `problem_count` (int): 需要选择的题目数量
- `average_accept_rate` (float): 目标平均通过率（0-1）
- `average_used_times` (int): 允许的平均使用次数
- `allow_recent_used` (bool): 是否允许使用近6个月用过的题目
- `allowed_types` (list[str]): 允许的题目类型标签列表
### 返回结构
```
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
```

---

## `/api/contest/filter` (POST)
*文件位置*: `online_judge/api/contest/show.py`

**描述**: 根据POST请求中的JSON参数过滤比赛(通过JSON Body传递参数)

### 参数说明
- `title` (str, 可选): 比赛标题模糊搜索关键词,支持部分匹配
- `holder_name` (str, 可选): 主办方名称精确匹配(区分大小写)
### 返回结构
```
list[dict]: 过滤后的比赛数据列表,每个字典包含:
        - contest_id (int): 比赛唯一标识符
        - contest_title (str): 比赛标题
        - holder_id (int): 主办用户ID
        - holder_name (str): 主办用户名称
        - start_time (str): 比赛开始时间(Wed, 26 Feb 2025 08:00:00 GMT)
        - end_time (str): 比赛结束时间(Wed, 26 Feb 2025 08:00:00 GMT)
        - information (str): 比赛描述信息
```

---

## `/api/contest/getinfo/<int:contest_id>` (GET)
*文件位置*: `online_judge/api/contest/show.py`

**描述**: (要求jwt_token)    
根据GET请求中的 contest_id(int) 获得比赛具体信息

### 参数说明
- `contest_id` (int): 比赛编号
### 返回结构
```
dict: 比赛信息 (包含比赛id, 比赛标题, 管理人id, 管理人名字, 起始时间, 结束时间, 比赛信息, 题目编号, 排行榜)
    TODO: 加一个ranklist例子
```

---

## `/api/contest/get_contest_user_solved_problem/<int:contest_id>` (POST)
*文件位置*: `online_judge/api/contest/show.py`

**描述**: 获取指定比赛中用户已解决的题目列表

### 参数说明
- `contest_id` (int): 路径参数,比赛唯一标识符
- (通过JWT Token获取用户身份)
### 返回结构
```
list[int]: 用户已解决的题目ID列表,格式示例:
        [103, 105, 107]
    数据结构说明:
        - 每个元素为题目唯一标识符(整数)
        - 按实际解决顺序排序
```

---

## `/api/contest/get_all_user/<int:contest_id>` (GET)
*文件位置*: `online_judge/api/contest/show.py`

**描述**: 获取指定比赛的所有参赛用户

### 参数说明
- `contest_id` (int): 路径参数,比赛唯一标识符
### 返回结构
```
list[int]: 参赛用户ID列表,格式示例:
        [1001, 1003, 1005]
    数据结构说明:
        - 每个元素为用户唯一标识符(整数)
        - 列表按用户加入比赛的时间排序
```

---

## `/api/contest/get_all_submission/<int:contest_id>` (GET)
*文件位置*: `online_judge/api/contest/show.py`

**描述**: 获取所有在比赛中的所有提交记录

### 参数说明
- `contest_id` (int): 路径参数,比赛唯一标识符
- (通过JWT Token获取用户身份)
### 返回结构
```
list[dict]: 提交记录列表,每个字典包含:
        - submission_id (int): 提交唯一标识符
        - problem_id (int): 题目唯一标识符
        - submit_time (str): 提交时间(Wed, 26 Feb 2025 08:00:00 GMT)
        - language (str): 编程语言(如"python"/"cpp")
        - status (str): 判题状态(枚举值:"Accepted", "WrongAnswer"等)
        - time_used (int): 耗时(毫秒)
        - memory_used (int): 内存使用(MB)
    示例结构:
        [{
            "submission_id": 1,
            "problem_id": 1,
            "submit_time": "Wed, 26 Feb 2025 08:00:00 GMT",
            "language": "python",
            "status": "Accepted",
            "time_used": 500,
            "memory_used": 128
        }]
```

---

## `/api/contest/get_contest_user_submission/<int:contest_id>` (GET)
*文件位置*: `online_judge/api/contest/show.py`

**描述**: 获取指定用户在比赛中的所有提交记录

### 参数说明
- `contest_id` (int): 路径参数,比赛唯一标识符
- (通过JWT Token获取用户身份)
### 返回结构
```
list[dict]: 提交记录列表,每个字典包含:
        - submission_id (int): 提交唯一标识符
        - problem_id (int): 题目唯一标识符
        - submit_time (str): 提交时间(Wed, 26 Feb 2025 08:00:00 GMT)
        - language (str): 编程语言(如"python"/"cpp")
        - status (str): 判题状态(枚举值:"Accepted", "WrongAnswer"等)
        - time_used (int): 耗时(毫秒)
        - memory_used (int): 内存使用(MB)
    示例结构:
        [{
            "submission_id": 1,
            "problem_id": 1,
            "submit_time": "Wed, 26 Feb 2025 08:00:00 GMT",
            "language": "Python",
            "status": "Accepted",
            "time_used": 500,
            "memory_used": 128
        }]
```

---

## `/api/contest/update_contest_info/<int:contest_id>` (POST)
*文件位置*: `online_judge/api/contest/update.py`

**描述**: 更新比赛基础信息接口

JWT验证:
- 需要在请求头携带有效JWT Token
- Token中必须包含用户权限信息

访问权限:
- 比赛创建者(holder_id与用户ID匹配)
- 管理员用户(用户权限power >=2)

### 参数说明
- `contest_id` (int): 路径参数,比赛唯一标识符
- (通过JWT Token获取用户身份)
- Returns:

---

## `/api/contest/update_contest_user/<int:contest_id>` (POST)
*文件位置*: `online_judge/api/contest/update.py`

**描述**: 全量更新比赛的关联用户列表

用请求中提供的用户ID列表替换当前比赛所有关联用户,执行原子化的添加/删除操作。
要求有效的JWT认证且用户具备管理员权限。

### 参数说明
- `contest_id` (int): 路径参数,目标比赛的唯一标识符
- `users` (list[int], optional): 请求体JSON中的用户ID列表。示例: [1001, 1003, 1005]
### 返回结构
```
JSON响应:
    - 成功 (200):
        {
            "success": True,
            "added": [1005, 1006],  # 本次新增的用户ID
            "removed": [1002],       # 本次移除的用户ID
            "total": 3               # 更新后的用户总数
        }
```

---

## `/api/contest/update_problems/<int:contest_id>` (POST)
*文件位置*: `online_judge/api/contest/update.py`

**描述**: 全量更新比赛关联的题目列表

用请求中的题目ID列表替换当前比赛所有关联题目,执行原子化更新操作。
要求有效的JWT且用户。
- 用户需满足以下任一条件:
    1. 比赛创建者 (contest.holder_id == user.id)
    2. 管理员用户 (user.power >= 2)

### 参数说明
- `contest_id` (int): 路径参数,目标比赛的唯一标识符
- `problem_ids` (list[int]): 请求体JSON中的题目ID列表。示例: [45, 67, 89]
### 返回结构
```
JSON响应
```

---

## `/api/contests` (POST)
*文件位置*: `online_judge/api/contest/update.py`

**描述**: 创建新的比赛

通过JSON请求体接收比赛信息,创建新比赛并返回创建结果。
要求有效的JWT认证。

### 参数说明
- (通过JSON Body传递参数)
- `title` (str): 比赛标题,必填,长度1-80字符
- `start_time` (str): 开始时间,RFC 1123格式字符串(如:Wed, 26 Feb 2025 08:00:00 GMT)
- `end_time` (str): 结束时间,RFC 1123格式字符串
- `information` (str, optional): 比赛描述信息,最大长度500字符
- `problem_ids` (list[int], optional): 初始关联题目ID列表
### 返回结构
```
JSON响应
```

---

## `/api/homework/generate` (POST)
*文件位置*: `online_judge/api/homework/gen_homework.py`

**描述**: 作业生成接口，根据要求自动生成作业题目集合。

从题库中选择符合要求的题目组合生成作业。需要教师权限。

### 参数说明
- `Authorization` (str): 请求头中的JWT令牌，格式：Bearer <token>
- JSON参数:
- `title` (str): 作业标题
- `description` (str, optional): 作业描述
- `start_time` (str): 开始时间,RFC 1123格式(如:Wed, 26 Feb 2025 08:00:00 GMT)
- `end_time` (str): 结束时间,RFC 1123格式
- `total_score` (int): 作业总分（默认100）
- `question_count` (int): 需要的题目数量
- `difficulty_range` (dict): 难度范围 {"min": 1, "max": 5}
- `question_types` (list[str]): 题目类型列表，可选值：["choice", "fill"]
- `tags` (list[str], optional): 题目标签列表
- `student_ids` (list[int], optional): 指定的学生ID列表
### 返回结构
```
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
```

---

## `/api/homework/filter` (POST)
*文件位置*: `online_judge/api/homework/show.py`

**描述**: 根据POST请求中的JSON参数过滤作业

### 参数说明
- `title` (str, optional): 作业标题模糊搜索关键词
- `holder_name` (str, optional): 创建者名称
### 返回结构
```
list[dict]: 过滤后的作业列表
```

---

## `/api/homework/show/<int:homework_id>` (GET)
*文件位置*: `online_judge/api/homework/show.py`

**描述**: 获取作业详细信息。

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

### 参数说明
- `homework_id` (int): 作业ID
### 返回结构
```
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
```

---

## `/api/homework/create` (POST)
*文件位置*: `online_judge/api/homework/update.py`

**描述**: 创建新作业

### 参数说明
- `title` (str): 作业标题
- `start_time` (str): 开始时间,RFC 1123格式(如:Wed, 26 Feb 2025 08:00:00 GMT)
- `end_time` (str): 结束时间,RFC 1123格式
- `description` (str, optional): 作业描述
- `question_list` (list[dict], optional): 初始题目列表 [{"question_id": int, "score": int}]
- `student_ids` (list[int], optional): 学生ID列表
### 返回结构
```
dict: 创建的作业信息
```

---

## `/api/homework/update/<int:homework_id>` (POST)
*文件位置*: `online_judge/api/homework/update.py`

**描述**: 更新作业信息

### 参数说明
- `homework_id` (int): 作业ID
- `title` (str, optional): 新标题
- `start_time` (str, optional): 新开始时间
- `end_time` (str, optional): 新结束时间
- `description` (str, optional): 新描述
- `question_list` (list[dict], optional): 新题目列表 [{"question_id": int, "score": int}]
- `student_ids` (list[int], optional): 新的学生ID列表
### 返回结构
```
dict: 更新后的作业信息
```

---

## `/api/homework/delete/<int:homework_id>` (POST)
*文件位置*: `online_judge/api/homework/update.py`

**描述**: 删除作业

### 参数说明
- `homework_id` (int): 作业ID
### 返回结构
```
dict: 操作结果
```

---

## `/api/homework/submit/<int:homework_id>` (POST)
*文件位置*: `online_judge/api/homework/update.py`

**描述**: 提交作业答案。

学生提交作业的接口，包含以下限制：
- 必须是作业的学生才能提交
- 必须在作业时间范围内提交
- 每份作业只能提交一次，提交后不能再次提交

### 参数说明
- `homework_id` (int): 作业ID
- `answer_list` (list): 答案列表 [{"question_id": int, "answer": str}, ...]
### 返回结构
```
JSON: {
        "success": bool,
        "score": int,      # 得分
        "submit_time": str  # GMT格式的提交时间
    }
    
Raises:
    400: 参数错误、作业未开始、作业已结束、已提交过
    403: 无权限（不是作业学生）
    404: 作业不存在
```

---

## `/api/problem/data/update/<int:problem_id>` (POST)
*文件位置*: `online_judge/api/problem/data.py`

**描述**: 更新题目测试数据（需题目创建者权限）

通过上传ZIP压缩包替换题目测试数据

### 参数说明
- `problem_id` (int): 路径参数，需要更新的题目ID
- `file` (File): POST表单文件字段，必须为ZIP格式的测试数据压缩包
### 返回结构
```
JSON响应:
    - 200 OK: {"OK": "Problem data updated successfully"}
    - 404 Bad Request: {"error": "错误描述"}
    - 403 Forbidden: {"error": "权限不足"}
    - 404 Not Found: {"error": "题目不存在"}

Raises:
    OSError: 文件系统操作异常
    zipfile.BadZipFile: 损坏的ZIP文件

Notes:
    1. ZIP文件结构示例:
       |
       |--1.in
       |--1.ans
    2. 数据要求：从1开始编号，最多30个测试点，一个.in对应一个.ans
```

---

## `/api/problem/filter` (POST)
*文件位置*: `online_judge/api/problem/filter.py`

**描述**: 题目筛选接口

Args (JSON Body):
    title (str, optional): 题目名称模糊搜索
    tags (list[str], optional): 必须包含的标签列表
    min_difficulty (int, optional): 难度下限(与max_difficulty必须成对使用)
    max_difficulty (int, optional): 难度上限
    min_used (int, optional): 使用次数下限(与max_used必须成对使用)
    max_used (int, optional): 使用次数上限
    recent_unused (bool, optional): 是否排除半年内使用过的题目(默认false)

### 返回结构
```
JSON Response:
        list[int]: 符合条件的题目ID列表
```

---

## `/api/problem/statement/get` (POST)
*文件位置*: `online_judge/api/problem/problem.py`

**描述**: 获取指定题目的详细信息说明

通过 JSON 请求体传递必要参数，验证用户对于题目的访问权限后返回题目详细信息，
需要满足以下条件之一：
1. 比赛模式：题目归属于指定比赛，且用户在参赛名单中
2. 练习模式：题目为公开状态，或用户是题目所有者且权限等级≥2

### 参数说明
- JSON Request Body:
- `problem_id` (int): 必填，要求查看的题目 ID
- `contest_id` (int): 可选的关联比赛 ID（默认值为 0表示非比赛模式）
### 返回结构
```
JSON Response:
        成功时返回 HTTP 200 和题目信息字典，包含：
            - id: 题目 ID
            - title: 题目标题
            - statement: 题目描述（Markdown 格式）
            - time_limit: 时间限制（秒）
            - memory_limit: 内存限制（MB）
            - 其他元数据...
        失败时返回对应的错误信息和状态码
```

---

## `/api/problem/statement/update/<int:problem_id>` (POST)
*文件位置*: `online_judge/api/problem/problem.py`

**描述**: 上传指定题目的信息

通过 JSON 请求体传递必要参数，验证用户对于题目的访问权限后返回题目详细信息

### 参数说明
- JSON Request Body:
- `title` (string): 题目名字
- `time_limit` (int): 题目时间限制
- `memory_limit` (int): 题目空间限制
- `statement` (string): 题目描述
- `tags` (list[int]): 题目标签
- Returns:

---

## `/api/problem/create` (POST)
*文件位置*: `online_judge/api/problem/problem.py`

**描述**: 创建新题目

### 参数说明
- JSON Request Body:
- `title` (string): 题目标题（必填）
- `time_limit` (int): 时间限制 ms（必填）
- `memory_limit` (int): 内存限制 MB（必填）
- `difficulty` (int): 难度
- `is_public` (bool): 是否公开
- `statement` (string): 题目描述 Markdown（必填）
- `tags` (list[string]): 标签名称列表（默认空列表）
### 返回结构
```
成功：HTTP 200 和包含 problem_id 的JSON
    失败：对应错误状态码和描述
```

---

## `/api/problem/submit` (POST)
*文件位置*: `online_judge/api/problem/submit.py`

**描述**: 处理代码提交请求，支持比赛/练习两种模式。

用户提交代码后，系统将进行合法性检查并触发自动评测。比赛提交需满足：
- 用户在参赛名单中
- 提交时间在比赛时段内
- 题目属于比赛题目

### 参数说明
- JSON参数:
- `problem_id` (int): 必填，提交的题目ID
- `code` (str): 必填，用户提交的源代码
- `language` (str): 必填，编程语言（如python/cpp）
- `contest_id` (int, optional): 关联的比赛ID，默认0表示练习模式
- `submit_time` (str, optional): 提交时间（GMT格式），默认当前时间
### 返回结构
```
JSON: 包含提交ID的响应，格式：
        成功 (200):
            {
                "OK": "submission_id = <id>,ok!",
                "submission_id": <int>
            }
        错误时返回对应状态码和错误描述，例如：
```

---

## `/api/questions/filter` (POST)
*文件位置*: `online_judge/api/questions/filter.py`

**描述**: 筛选选择题或填空题

### 参数说明
- `title` (str, optional): 题目标题模糊搜索
- `type` (str, optional): 题目类型('choice'或'fill')
- `tags` (list[str], optional): 必须包含的标签列表
- `min_difficulty` (int, optional): 难度下限(与max_difficulty必须成对使用)
- `max_difficulty` (int, optional): 难度上限
- `min_used` (int, optional): 使用次数下限(与max_used必须成对使用)
- `max_used` (int, optional): 使用次数上限
- `creator_name` (str, optional): 创建者名称
### 返回结构
```
list[dict]: 符合条件的题目列表
```

---

## `/api/questions/get/<int:question_id>` (GET)
*文件位置*: `online_judge/api/questions/show.py`

**描述**: 获取选择题或填空题的详细信息。

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

### 参数说明
- `question_id` (int): 题目ID
### 返回结构
```
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
```

---

## `/api/questions/create` (POST)
*文件位置*: `online_judge/api/questions/update.py`

**描述**: 创建选择题或填空题

### 参数说明
- `title` (str): 题目标题
- `content` (str): 题目内容
- `question_type` (str): 题目类型('choice'或'fill')
- `answer` (str): 答案(选择题形如"AB"，填空题直接存答案)
- `options` (list[str], 仅选择题): 选项列表
- `options_count` (int, 仅选择题): 选项个数
- `explanation` (str, optional): 题目解析
- `difficulty` (int, optional): 难度(1-5,默认1)
- `is_public` (bool, optional): 是否公开(默认false)
- `tags` (list[str], optional): 标签列表
### 返回结构
```
dict: 创建的题目信息
```

---

## `/api/questions/update/<int:question_id>` (POST)
*文件位置*: `online_judge/api/questions/update.py`

**描述**: 更新选择题或填空题

### 参数说明
- `question_id` (int): 题目ID
- `title` (str, optional): 新标题
- `content` (str, optional): 新内容
- `options` (list[str], optional): 新选项列表(仅选择题)
- `answer` (str, optional): 新答案
- `explanation` (str, optional): 新解析
- `difficulty` (int, optional): 新难度(1-5)
- `is_public` (bool, optional): 是否公开
- `tags` (list[str], optional): 新标签列表
### 返回结构
```
dict: 更新后的题目信息
```

---

## `/api/questions/delete/<int:question_id>` (POST)
*文件位置*: `online_judge/api/questions/update.py`

**描述**: 删除选择题或填空题

### 参数说明
- `question_id` (int): 题目ID
### 返回结构
```
dict: 操作结果
```

---

## `/api/submission/filter` (POST)
*文件位置*: `online_judge/api/submission/show.py`

**描述**: 根据多条件筛选提交记录

支持通过组合多个查询参数过滤提交记录，返回分页后的结果集

### 参数说明
- `user_id` (int, optional): 筛选指定用户的提交记录
- `problem_id` (int, optional): 筛选指定题目的提交记录
- `contest_id` (int, optional): 筛选指定比赛的提交记录
- `language` (str, optional): 按编程语言过滤（枚举值：python/cpp）
### 返回结构
```
JSON: 包含分页信息的提交记录列表
    {
        "submissions": [
            {
                "id": 123,
                "problem_id": 456,
                "user_id": 789,
                "language": "python",
                "submit_time": "2023-08-20T14:30:00",
                "status": "Accepted",
                "time_used": 100,    // 单位：毫秒
                "memory_used": 2048  // 单位：KB
            },
            ...
        ],
        "pagination": {
            "total": 100,
            "current_page": 1,
            "per_page": 20
        }
    }

Raises:
    400 Bad Request: 参数格式错误
    500 Internal Server Error: 数据库查询异常
```

---

## `/api/submission/get/<int:submission_id>` (GET)
*文件位置*: `online_judge/api/submission/show.py`

**描述**: 获取指定提交记录的详细信息

### 参数说明
- `submission_id` (int): 路径参数，提交记录的唯一标识符
### 返回结构
```
JSON: 提交记录的完整信息
    {
        "id": 123,
        "code": "print('Hello World')",
        "language": "python",
        "user_id": 456,
        "problem_id": 789,
        "contest_id": 101,
        "submit_time": "2023-08-20T14:30:00",
        "status": "Accepted",
        "time_used": 100,      // 单位：毫秒
        "memory_used": 2048,   // 单位：KB
        "compile_error_info": ""  // 编译错误信息（如有）
    }

Raises:
    404 Not Found: 指定ID的提交记录不存在

Notes:
    1. 代码内容仅对提交者/管理员可见（待实现）
    2. 编译错误信息仅在状态为CompileError时返回
```

---
