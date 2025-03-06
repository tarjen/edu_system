from online_judge import db

problem_tag = db.Table('problem_tag',
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(80), index=True)
    user_id = db.Column(db.Integer, index=True)
    user_name = db.Column(db.String(80))

    time_limit = db.Column(db.Integer)
    memory_limit = db.Column(db.Integer)
    statement = db.Column(db.Text)

    difficulty = db.Column(db.Integer)
    accept_num = db.Column(db.Integer)
    submit_num = db.Column(db.Integer)
    is_public = db.Column(db.Boolean)
    used_times = db.Column(db.Integer)

    tags = db.relationship('Tag', secondary='problem_tag', backref='problems')

    def __init__(self, title, user_id,user_name,difficulty,statement,
                 is_public=False,time_limit=1000, memory_limit=256
                 ):
        self.title = title
        self.user_name = user_name
        self.user_id = user_id
        self.difficulty = difficulty

        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.statement = statement

        self.accept_num = 0
        self.submit_num = 0
        self.is_public = is_public
        self.used_times = 0

    def __repr__(self):
        return "<Problem %r>" % self.title

    def save(self):
        db.session.add(self)
        db.session.commit()

    def is_allowed_edit(self, user=None):
        if not user:
            return False
        if self.user_id == user.id or user.power >= 2 : 
            return True
        return False

    def is_allowed_use(self, user=None):
        if self.is_public:
            return True
        if not user:
            return False
        if self.user_id == user.id or user.power >= 2:
            return True
        return False

    def set_is_public(self, public):
        self.is_public = public
        self.save()
    def get_tags_string(self):
        tags_list = [tag.name for tag in self.tags]
        return ', '.join(tags_list) if tags_list else ""


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, index=True)  

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Tag %r>" % self.name

    def save(self):
        db.session.add(self)
        db.session.commit()

