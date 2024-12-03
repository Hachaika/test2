from db import db


class TestResult(db.Model):
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    mistakes = db.Column(db.Integer, nullable=False)
    time_spent = db.Column(db.Interval, nullable=False)
    table_index = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, mistakes, time_spent, table_index):
        self.user_id = user_id
        self.mistakes = mistakes
        self.time_spent = time_spent
        self.table_index = table_index

    def __repr__(self):
        return f'<TestResult user_id={self.user_id} table_index={self.table_index} mistakes={self.mistakes} time_spent={self.time_spent}>'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return f'<User name={self.name}>'


class Test(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mistakes = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Interval, nullable=False)
    table_index = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('tests', lazy=True))

    def __init__(self, user_id, time_spent, table_index):
        self.user_id = user_id
        self.time_spent = time_spent
        self.table_index = table_index

    def __repr__(self):
        return f'<Test user_id={self.user_id} table_index={self.table_index} mistakes={self.mistakes} time_spent={self.time_spent}>'

