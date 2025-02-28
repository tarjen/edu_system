from online_judge import app,db
from online_judge import db
from online_judge.models import Contest, Problem, Submission
from datetime import datetime
import time

@app.cli.command()  # 注册为命令,可以传入 name 参数来自定义命令
def testdb():
    db.drop_all()
    db.create_all()
    # 生成 Contest 实例
    contests = [
        Contest(title='Contest 1', start_time=datetime(2025, 2, 26, 8, 0, 0), end_time=datetime(2025, 2, 27, 8, 0, 0), holder_id=1, holder_name='Holder 1'),
        Contest(title='Contest 2', start_time=datetime(2025, 3, 5, 9, 0, 0), end_time=datetime(2025, 3, 6, 9, 0, 0), holder_id=2, holder_name='Holder 2'),
        Contest(title='Contest 3', start_time=datetime(2025, 3, 12, 10, 0, 0), end_time=datetime(2025, 3, 13, 10, 0, 0), holder_id=3, holder_name='Holder 3'),
        Contest(title='Contest 4', start_time=datetime(2025, 3, 19, 11, 0, 0), end_time=datetime(2025, 3, 20, 11, 0, 0), holder_id=4, holder_name='Holder 4'),
        Contest(title='Contest 5', start_time=datetime(2025, 3, 26, 12, 0, 0), end_time=datetime(2025, 3, 27, 12, 0, 0), holder_id=5, holder_name='Holder 5')
    ]

    # 生成 Problem 实例
    problems = [
        Problem(title='Problem 1', user_id=1, user_name='User 1', time_limit=1, memory_limit=128, tags='tag1,tag2', is_public=True),
        Problem(title='Problem 2', user_id=2, user_name='User 2', time_limit=2, memory_limit=256, tags='tag3,tag4', is_public=True),
        Problem(title='Problem 3', user_id=3, user_name='User 3', time_limit=3, memory_limit=512, tags='tag5,tag6', is_public=True),
        Problem(title='Problem 4', user_id=4, user_name='User 4', time_limit=4, memory_limit=1024, tags='tag7,tag8', is_public=True),
        Problem(title='Problem 5', user_id=5, user_name='User 5', time_limit=5, memory_limit=2048, tags='tag9,tag10', is_public=True)
    ]


    # 生成 Submission 实例
    submissions = [
        Submission(code='Submitted code for Problem 1', language='Python', user_id=1, problem_id=1, contest_id=0, submit_time=datetime.now()),
        Submission(code='Submitted code for Problem 2', language='C++', user_id=2, problem_id=2, contest_id=0, submit_time=datetime.now()),
        Submission(code='Submitted code for Problem 3', language='Rust', user_id=3, problem_id=3, contest_id=0, submit_time=datetime.now()),
        Submission(code='Submitted code for Problem 4', language='Python', user_id=4, problem_id=4, contest_id=0, submit_time=datetime.now()),
        Submission(code='Submitted code for Problem 5', language='C++', user_id=5, problem_id=5, contest_id=0, submit_time=datetime.now())
    ]

    # 将实例添加到数据库会话中
    for contest in contests:
        db.session.add(contest)

    for problem in problems:
        db.session.add(problem)

    for submission in submissions:
        db.session.add(submission)

    # 提交更改到数据库
    db.session.commit()

    # 打印提示信息
    print("模型实例创建成功！")