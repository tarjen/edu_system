import os
import click
from datetime import datetime
from flask import current_app
from flask.cli import with_appcontext
from online_judge import db  # 替换为实际导入方式
from online_judge.models import  Contest, Problem, ContestUser, Submission, Tag  # 替换为实际模型路径


class User:
    def __init__(self,id,username,power):
        self.id=id
        self.username=username
        self.power=power

def register_commands(app):
    @app.cli.command("gen_database")
    @with_appcontext
    def gen_database():
        """Initialize the database with test data"""
        
        # 删除本地数据库文件
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.split('sqlite:///')[-1]
            if os.path.exists(db_path):
                os.remove(db_path)
                click.echo(f"已删除旧数据库: {db_path}")

        # 创建数据库表
        db.create_all()
        click.echo("数据库表结构已创建")

        # 创建测试用户（需先于其他数据创建）
        users = [
            User(id=1, username="admin", power=2),
            User(id=2, username="user1", power=1),
            User(id=3, username="creator", power=1)
        ]
        click.echo("测试用户已创建")

        # 创建比赛数据
        contests = [
            Contest(
                title="Admin's Contest",
                start_time=datetime(2025, 1, 1, 8, 0, 0),
                end_time=datetime(2025, 1, 2, 8, 0, 0),
                holder_id=1,
                holder_name="admin"
            ),
            Contest(
                title="User's Contest",
                start_time=datetime(2025, 2, 1, 9, 0, 0),
                end_time=datetime(2025, 2, 2, 9, 0, 0),
                holder_id=3,
                holder_name="creator"
            )
        ]
        db.session.bulk_save_objects(contests)
        db.session.commit()
        click.echo("比赛数据已创建")

        # 创建题目数据
        problems = [
            Problem(
                title="Problem 1",
                statement="A+B",
                user_id=1,
                user_name="admin",
                difficulty=1,
                is_public=True
            ),
            Problem(
                title="Problem 2",
                statement="data1:(input,output),data2:(intput2,output2)",
                user_id=1,
                user_name="admin",
                difficulty=2,
                is_public=False
            )
        ]
        db.session.bulk_save_objects(problems)
        db.session.commit()
        click.echo("题目数据已创建")

        # 关联比赛题目
        contest1 = Contest.query.get(1)
        contest1.update_problems(problem_ids=[1, 2], current_user=users[0])
        click.echo("比赛题目关联完成")

        # 创建比赛用户关联
        contest_users = [
            ContestUser(contest_id=1, user_id=1),
            ContestUser(contest_id=1, user_id=2)
        ]
        db.session.bulk_save_objects(contest_users)
        db.session.commit()
        click.echo("比赛用户关联完成")

        # 创建标签
        tags = [
            Tag(name='algorithm'),
            Tag(name='data-structure')
        ]
        db.session.bulk_save_objects(tags)
        db.session.commit()
        click.echo("标签数据已创建")

        click.secho("数据库初始化完成！", fg='green')
