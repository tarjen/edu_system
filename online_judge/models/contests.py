from flask import jsonify
from online_judge import db
from online_judge.models.problems import Problem
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy import exc
import time
import json

PENALTY_PER_ATTEMPT = 20

contest_problem = db.Table('contest_problem',
    db.Column('contest_id', db.Integer, db.ForeignKey('contest.id'), primary_key=True),
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
)

class ContestUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey("contest.id"), index=True)
    user_id = db.Column(db.Integer, index=True)
    score_details = db.Column(db.Text)

    # score = db.Column(db.Integer)
    # time_spent = db.Column(db.Integer)

    def __init__(self, contest_id, user_id):
        self.contest_id = contest_id
        self.user_id = user_id
        self.score_details = "{}"

        # self.score = 0
        # self.time_spent = 0

    def __repr__(self):
        return "<ContestPlayer contest_id:%s user_id=%s score_details=%s>" % \
               (self.contest_id, self.user_id, self.score_details)
    def calculate_score(self,problem_ids):
        """
        Return (score,penalty) by given problem_ids
        Args:
            problem_ids (integer list): 
        Returns:
            score,penalty
        """
        score = 0
        penalty = 0
        score_details = json.loads(self.score_details)
        for problem_id in problem_ids:
            pid = str(problem_id)
            if pid in score_details:
                if score_details[problem_id]["solve_time"] != -1:
                    score += 1
                    penalty += score_details["solve_time"] + score_details[pid]["attempts"] * PENALTY_PER_ATTEMPT
        return score,penalty

    def update_score(self, submission):
        score_details = json.loads(self.score_details)
        pid = str(submission.problem_id)
        if pid not in score_details:
            score_details[pid] = {}
            score_details[pid]["solve_time"]=-1
            score_details[pid]["attempts"]=0;
        else:
            if score_details[pid]["solve_time"] != -1: # Have accepted
                return
            
        if submission.status == "Accepted":
            contest_start_time = Contest.query.filter_by(id=self.contest_id).first().start_time
            score_details["solve_time"] = (submission.submit_time-contest_start_time).total_seconds() // 60
            # self.time_spent += score_details["solve_time"] + score_details[pid]["attempts"] * PENALTY_PER_ATTEMPT
            # self.score += 1
        else:
            score_details[pid]["attempts"] += 1

        self.score_details = json.dumps(score_details)
        self.save()

    def get_score_details(self):
        return json.loads(self.score_details)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    start_time = db.Column(DateTime)
    end_time = db.Column(DateTime)

    holder_id = db.Column(db.Integer)
    holder_name = db.Column(db.String(80))

    information = db.Column(db.Text)
    problems = db.relationship('Problem', 
                            secondary=contest_problem,
                            backref=db.backref('contests', lazy='dynamic'),
                            lazy='dynamic')  # 新增多对多关系

    def __init__(self, title, start_time, end_time, holder_id, holder_name, information=""):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.holder_id = holder_id
        self.holder_name = holder_name
        self.information = information

    def add_users(self, user_ids):
        existing_ids = { 
            cu.user_id for cu in ContestUser.query.filter_by(contest_id=self.id)
                                                .filter(ContestUser.user_id.in_(user_ids))
                                                .with_entities(ContestUser.user_id)
                                                .all() 
        }
        
        new_users = [
            ContestUser(contest_id=self.id, user_id=uid)
            for uid in user_ids if uid not in existing_ids
        ]
        
        if new_users:
            db.session.bulk_save_objects(new_users)
            db.session.commit()

    def delete_users(self, user_ids):
        if user_ids:
            ContestUser.query.filter(
                ContestUser.contest_id == self.id,
                ContestUser.user_id.in_(user_ids)
            ).delete(synchronize_session=False)
            db.session.commit()
    def get_current_users(self):
        return [u.user_id for u in 
                ContestUser.query.filter_by(contest_id=self.id)
                                .with_entities(ContestUser.user_id)
                                .all()]
    
    def add_problem(self, problem_id, current_user=None):
        """
        添加题目到比赛(需满足以下条件之一):
        1. 题目是公开的
        2. 题目属于比赛创建者
        3. 当前用户是管理员(power >=2)
        """
        problem = Problem.query.filter_by(id=problem_id).first()
        if not problem:
            raise ValueError(f"Problem {problem_id} not found")

        # 权限验证
        if not (problem.is_public 
                or problem.user_id == self.holder_id
                or (current_user and current_user.power >= 2)):
            raise PermissionError(f"No permission to add problem {problem_id}")

        # 检查是否已关联
        if self.problems.filter(contest_problem.c.problem_id == problem_id).first():
            return  # 已存在则跳过

        try:
            # 原子操作更新使用次数
            problem.used_times += 1
            self.problems.append(problem)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise RuntimeError(f"Database error: {str(e)}")

    def update_problems(self, problem_ids, current_user):
        """
        批量更新比赛题目(全量替换)
        需要所有题目都满足添加条件
        """
        # 预检查所有题目权限
        problems = Problem.query.filter(Problem.id.in_(problem_ids)).all()
        if len(problems) != len(problem_ids):
            invalid_ids = set(problem_ids) - {p.id for p in problems}
            raise ValueError(f"Invalid problem IDs: {invalid_ids}")

        for problem in problems:
            if not (problem.is_public 
                    or problem.user_id == self.holder_id
                    or current_user.power >= 2):
                raise PermissionError(f"No permission for problem {problem.id}")

        try:
            # 开启事务
            db.session.begin_nested()

            # 清空原有题目
            original_problems = self.problems.all()
            for p in original_problems:
                p.used_times -= 1
            self.problems = []

            # 添加新题目
            for pid in problem_ids:
                self.add_problem(pid, current_user)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # 回滚使用次数
            for p in original_problems:
                p.used_times += 1
            raise RuntimeError(f"Update failed: {str(e)}")

    def get_problems(self):
        return [p.id for p in self.problems.all()]  # 通过关系直接获取
    
    def get_ranklist(self):
        sorted_users = []
        contest_users = ContestUser.query.filter_by(contest_id=self.id)
        problem_ids = self.get_problems()
        # 计算每个用户的分数和惩罚,并存储在一个临时列表中
        for user in contest_users:
            score, penalty = user.calculate_score(problem_ids)
            sorted_users.append({
                "user_id": user.user_id,
                "score": score,
                "penalty": penalty,
                "score_details": user.get_score_details(),
            })
        
        # 按照规则排序用户列表
        sorted_users = sorted(sorted_users, key=lambda x: (-x["score"], x["penalty"]))
        
        # 构建JSON结果
        result = []
        for user_data in sorted_users:
            result.append({
                "user_id": user_data["user_id"],
                "score": user_data["score"],
                "penalty": user_data["penalty"],
                "score_details": user_data["score_details"]
            })
        return result

    def __repr__(self):
        return "<Contest %r>" % self.title

    def save(self):
        db.session.add(self)
        db.session.commit()

    def is_allowed_edit(self, user):
        if user and user.power >= 2:
            return True
        if user and user.id == self.holder_id:
            return True
        return False
    
    def is_allowed_view(self, user):
        contestuser=ContestUser.query.filter_by(contest_id=self.id,user_id=user.id).first()
        return self.is_allowed_edit(user) or contestuser is not None

    def is_running(self, now=None):
        if not now:
            now = datetime.now()
        return self.start_time <= now and now <= self.end_time

   
