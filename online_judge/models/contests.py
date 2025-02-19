from online_judge import db
from online_judge.models.problems import Problem
from sqlalchemy import DateTime
from datetime import datetime
import time
import json

PENALTY_PER_ATTEMPT = 20

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
        self.score_details = ""

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
            if problem_id in score_details:
                if score_details[problem_id]["solve_time"] != -1:
                    score += 1
                    penalty += score_details["solve_time"] + score_details[problem_id]["attempts"] * PENALTY_PER_ATTEMPT
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
            contest_begin_time = Contest.query.filter_by(contest_id=self.contest_id).first().begin_time
            score_details["solve_time"] = (submission.submit_time-contest_begin_time).total_seconds() // 60
            # self.time_spent += score_details["solve_time"] + score_details[pid]["attempts"] * PENALTY_PER_ATTEMPT
            # self.score += 1
        else:
            score_details[pid]["attempts"] += 1

        self.score_details = json.dumps(score_details)

    def get_score_details(self):
        return json.loads(self.score_details)

    def save(self):
        db.session.add(self)
        db.session.commit()


class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    start_time = db.Column(DateTime)
    end_time = db.Column(DateTime)

    holder_id = db.Column(db.Integer, index=True)
    holder_name = db.Column(db.String(80))

    information = db.Column(db.Text)
    problem_ids = db.Column(db.Text) # save use text represent problems id,split by ","

    def add_users(self,user_ids):
        """
        add Paticipants(Users) by a user_id list
        if the user is in the contest,then pass it
        Args:
            user_ids (integer list): 
        Returns:
            None
        """
        for user_id in user_ids:
            contestuser = ContestUser.query.filter_by(contest_id=self.id,user_id=user_id).first()
            if contestuser is None:
                ContestUser(contest_id=self.id,user_id=user_id).save()

    
    def add_problem(self, problem_id):
        """
        add problems by a problem_id 
        if the problem is in the contest,then pass it
        Args:
            problem_id (int): 
        Returns:
            None
        """
        contest_problems_int = self.get_problems()
        if problem_id in contest_problems_int:
            return
        if self.problem_ids:
            self.problem_ids += f",{problem_id}"
        else:
            self.problem_ids = f"{problem_id}"
    def update_problem(self, problem_ids):
        """
        update problems by a problem_id list 
        Args:
            problem_ids (integer list): 
        Returns:
            None
        """
        self.problem_ids=""
        for problem_id in problem_ids:
            if self.problem_ids:
                self.problem_ids += f",{problem_id}"
            else:
                self.problem_ids = f"{problem_id}"
    def get_problems(self):
        """
        Return problems in contest

        Args:
            None
        Returns:
            problem_ids (integer list): 
        """
        contest_problems = self.problem_ids.split(",")
        contest_problems_int = [int(id) for id in contest_problems]
        return contest_problems_int
    def get_ranklist(self):
        """
        ranklist format(dict):
            userid,score,penalty,score_details
        score_details format(dict):
            problem_id,solve_time,attempt
        Args:
            None
        Returns:
            ranklist (integer list): 
        """
        sorted_users = []
        contest_users = ContestUser.query.filter_by(contest_id=self.id)
        # 计算每个用户的分数和惩罚，并存储在一个临时列表中
        for user in contest_users:
            score, penalty = user.calculate_score(self.problem_ids)
            sorted_users.append({
                "user_id": user.user_id,
                "score": score,
                "penalty": penalty,
                "score_details": user.get_score_details(self.problem_ids)
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
        
        # 将结果写入JSON文件
        with open('sorted_contest_users.json', 'w') as file:
            json.dump(result, file, indent=4)
        
        return result
    def __init__(self, title, start_time, end_time, holder):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.holder = holder


    def __repr__(self):
        return "<Contest %r>" % self.title

    def save(self):
        db.session.add(self)
        db.session.commit()

    def is_allowed_edit(self, user=None):
        if user and user.priviledge >= 2:
            return True
        if user and user.id == self.holder.id:
            return True
        return False

    def is_running(self, now=None):
        if not now:
            now = datetime.now()
        return self.start_time <= now and now <= self.end_time

   
