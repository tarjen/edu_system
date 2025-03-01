from online_judge import db
from online_judge.models.contests import Contest,ContestUser
from online_judge.models.problems import Problem
from sqlalchemy import Enum
from sqlalchemy import DateTime
import time


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text)
    language = db.Column(Enum("cpp","python", name="language_type"))
    user_id = db.Column(db.Integer, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), index=True)
    submit_time = db.Column(DateTime)  
    contest_id = db.Column(db.Integer, nullable = True, index=True)

    status = db.Column(Enum("Pending","Accepted","WrongAnswer","TimeLimitExceeded","IdlenessLimitExceeded",
        "RuntimeError","SystemError","CompileError", name="status_type"))
    time_used = db.Column(db.Integer)
    memory_used = db.Column(db.Integer)
    compile_error_info = db.Column(db.Text)

    def __init__(self, code, language, user_id, problem_id, contest_id, submit_time):
        self.code = code
        self.language = language
        self.user_id = user_id
        self.problem_id = problem_id
        self.contest_id = contest_id
        self.submit_time = submit_time

        self.status = "Pending"
        self.time_used = 0
        self.memory_used = 0
        self.compile_error_info = ""

    def __repr__(self):
        return "<JudgeState %r>" % self.id

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update_result_from_pending(self, status, time_used=0, memory_used=0,ce_info=""):
        if self.status != "Pending":
            raise ValueError(f"the submission has been updated,error id={self.id}")
        self.status = status
        self.time_used = time_used
        self.memory_used = memory_used
        if(self.status == "CompileError" or self.status == "SystemError"):
            self.compile_error_info = ce_info
            self.save()
            return
        #update problems info
        problem = Problem.query.filter_by(id=self.problem_id).first()
        problem.submit_num += 1
        if self.status == "Accepted":
            problem.accept_num += 1
        problem.save()
        self.save()
        #update contests info

        if self.contest_id is None:
            return
        contest_end_time = Contest.query.filter_by(id=self.contest_id).first().end_time
        if self.problem_id != None and self.submit_time <= contest_end_time:
            contestuser = ContestUser.query.filter_by(contest_id=self.contest_id,user_id=self.user_id).first()
            if contestuser is None:
                raise IndexError(f"Contest-User is incorrect id={self.id},contest_id={self.contest_id},user_id={self.user_id}")
            contestuser.update_score(self)
