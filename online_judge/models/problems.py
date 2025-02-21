from online_judge import db

tags_table = db.Table('problem_tags',
                      db.Column('tag_id', db.Integer, db.ForeignKey('problem_tag.id'), index=True),
                      db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), index=True)
                      )


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(80), index=True)
    user_id = db.Column(db.Integer, index=True)
    user_name = db.Column(db.String(80))

    time_limit = db.Column(db.Integer)
    memory_limit = db.Column(db.Integer)

    tags = db.relationship('ProblemTag', secondary=tags_table,
                           backref=db.backref('problems', lazy='dynamic'))

    accept_num = db.Column(db.Integer)
    submit_num = db.Column(db.Integer)
    is_public = db.Column(db.Boolean)
    used_times = db.Column(db.Integer)

    def __init__(self, title, user_id,user_name,
                 time_limit=1000, memory_limit=256
                 ):
        self.title = title
        self.user_name = user_name
        self.user_id = user_id

        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.accept_num = 0
        self.submit_num = 0
        self.is_public = False
        self.used_time = 0

    def __repr__(self):
        return "<Problem %r>" % self.title

    def save(self):
        db.session.add(self)
        db.session.commit()

    def is_allowed_edit(self, user=None):
        if not user:
            return False
        if self.user_id == user.id or user.privilege >= 2 : #TODO check the privilge of user
            return True
        return False

    def is_allowed_use(self, user=None):
        if self.is_public:
            return True
        if not user:
            return False
        if self.user_id == user.id or user.privilege >= 2:
            return True
        return False

    def set_is_public(self, public):
        self.is_public = public
        self.save()
    def get_tags_string(self):
        tags_list = [tag.name for tag in self.tags]
        return ', '.join(tags_list) if tags_list else ""


class ProblemTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), index=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Tag %r>" % self.name

    def save(self):
        db.session.add(self)
        db.session.commit()