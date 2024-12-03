from flask import Flask, render_template, redirect, url_for, request
from db import db
from models import User
import time
from datetime import timedelta
from random import shuffle
from flask import session

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/shulte'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '77277'
db.init_app(app)


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')


class TestResult(db.Model):
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mistakes = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Interval, nullable=False)
    table_index = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('test_results', lazy=True))

    __table_args__ = {'extend_existing': True}

    def __init__(self, user_id, mistakes, time_spent, table_index):
        self.user_id = user_id
        self.mistakes = mistakes
        self.time_spent = time_spent
        self.table_index = table_index

    def __repr__(self):
        return f'<TestResult user_id={self.user_id} table_index={self.table_index} mistakes={self.mistakes} time_spent={self.time_spent}>'


class TestTable:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.size = rows * cols
        self.table = self.generate_table()
        self.current_index = 0
        self.mistakes = 0

    def generate_table(self):
        numbers = list(range(1, self.size + 1))
        shuffle(numbers)
        table = []
        for i in range(self.rows):
            table.append(numbers[i * self.cols:(i + 1) * self.cols])
        return table

    def check_number(self, number):
        if self.table[self.current_index // self.cols][self.current_index % self.cols] == number:
            self.current_index += 1
        else:
            self.mistakes += 1

    def is_completed(self):
        return self.current_index == self.size

    def get_time(self, start_time):
        return timedelta(seconds=int(time.time() - start_time))


@app.route('/test', methods=['GET', 'POST'])
def test():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    # Получаем данные из сессии
    test_session_data = session.get('test_session', None)

    if test_session_data is None:
        test_session_data = {
            'user_id': user_id,
            'current_table_index': 0,
            'mistakes': 0,
            'start_time': None
        }
        session['test_session'] = test_session_data  # сохраняем в сессии

    current_table_index = test_session_data['current_table_index']
    mistakes = test_session_data['mistakes']

    # Создаем таблицу
    table = TestTable(5, 5)  # Создаем новую таблицу с размерами 5x5

    # Если таблица не начата, то начинаем
    if test_session_data['start_time'] is None:
        test_session_data['start_time'] = time.time()

    if request.method == 'POST':
        # Обрабатываем ответы пользователя
        for number in request.form.getlist('numbers'):
            table.check_number(int(number))

        # если таблица завершена
        if table.is_completed():
            results = {
                'mistakes': table.mistakes,
                'time_spent': table.get_time(test_session_data['start_time'])
            }

            # Сохранение результата для текущей таблицы
            test_result = TestResult(
                user_id=user_id,
                mistakes=results['mistakes'],
                time_spent=results['time_spent'],
                table_index=current_table_index
            )
            db.session.add(test_result)
            db.session.commit()

            # Переход к следующей таблице или к результатам
            if current_table_index < 4:  # если это не последняя таблица
                test_session_data['current_table_index'] = current_table_index + 1
                return redirect(url_for('test', user_id=user_id))
            else:
                # Очистка сессии, когда все таблицы завершены
                session.pop('test_session', None)
                return redirect(url_for('result', user_id=user_id))

    # Показ таблицы
    time_spent = int(time.time() - test_session_data['start_time']) if test_session_data['start_time'] else 0
    return render_template('test.html',
                           table=table.table,
                           user_id=user_id,
                           table_index=current_table_index,
                           mistakes=mistakes,
                           time_spent=time_spent)


@app.route('/result')
def result():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    test_results = TestResult.query.filter_by(user_id=user_id).all()
    total_mistakes = sum(result.mistakes for result in test_results)
    total_time = sum(int(result.time_spent.total_seconds()) for result in test_results)

    return render_template('result.html',
                           test_results=test_results,
                           total_mistakes=total_mistakes,
                           total_time=total_time)


# Маршрут для страницы психолога
@app.route('/psychologist', methods=['GET', 'POST'])
def psychologist():
    users = User.query.all()  # Получаем всех пользователей

    if request.method == 'POST':
        # Обрабатываем отправку формы для назначения теста
        for user in users:
            # Получаем значение чекбокса для каждого пользователя
            test_assigned = request.form.get(f'assign_test_{user.id}')
            if test_assigned:  # Если чекбокс выбран
                user.test_assigned = True
            else:
                user.test_assigned = False
            db.session.commit()

        return redirect(url_for('psychologist'))  # Перенаправляем обратно на страницу

    return render_template('psychologist.html', users=users)


# Страница добавления пользователя
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Добавляем нового пользователя в базу
        new_user = User(name=name, email=email)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))  # Перенаправляем обратно на главную страницу

    return render_template('add_user.html')


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Удаляет все таблицы
        db.create_all()  # Пересоздаёт таблицы
    app.run(debug=True)
