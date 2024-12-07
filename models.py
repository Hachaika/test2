from db import db
from datetime import datetime


class Result(db.Model):
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
    role = db.Column(db.String(50), nullable=False)  # Роль пользователя
    test_assigned = db.Column(db.Boolean, default=False)  # Флаг для назначения теста

    def __init__(self, name, email, role='subject'):
        self.name = name
        self.email = email
        self.role = role

    @property
    def test_passed(self):
        return Result.query.filter_by(user_id=self.id).count() > 0


class Score(db.Model):
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    efficiency_score = db.Column(db.Float, nullable=False)
    workability_score = db.Column(db.Float, nullable=False)
    mental_score = db.Column(db.Float, nullable=False)

    def __init__(self, efficiency_score, workability_score, mental_score):
        self.efficiency_score = efficiency_score
        self.workability_score = workability_score
        self.mental_score = mental_score

    def __repr__(self):
        return f'<Score id={self.id} efficiency={self.efficiency_score} workability={self.workability_score} mental={self.mental_score}>'
