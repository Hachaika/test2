from flask import Flask, render_template, redirect, url_for, request, jsonify
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


@app.route('/')
def index():
    users = User.query.all()  # Получаем всех пользователей
    return render_template('index.html', users=users)


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
        return f'<TestResult user_id={self.user_id} table_index={self.table_index} mistakes={self.mistakes} ' \
               f'time_spent={self.time_spent}>'


class TestTable:
    def __init__(self, rows, cols, numbers=None):
        self.rows = rows
        self.cols = cols
        self.size = rows * cols
        if numbers is None:
            self.table = self.generate_table()
        else:
            self.table = numbers
        self.current_index = 0
        self.mistakes = 0

    def generate_table(self):
        numbers = list(range(1, self.size + 1))
        shuffle(numbers)
        table = [numbers[i * self.cols:(i + 1) * self.cols] for i in range(self.rows)]
        return table

    def check_number(self, number):
        expected_number = self.current_index + 1
        if number == expected_number:
            self.current_index += 1
            return True
        else:
            self.mistakes += 1
            return False

    def is_completed(self):
        return self.current_index == self.size

    def get_state(self):
        return {
            "table": self.table,
            "current_index": self.current_index,
            "mistakes": self.mistakes
        }

    @classmethod
    def from_state(cls, rows, cols, state):
        table = state['table']
        obj = cls(rows, cols, numbers=table)
        obj.current_index = state['current_index']
        obj.mistakes = state['mistakes']
        return obj


@app.route('/logout')
def logout():
    session.clear()  # Очистка всех данных из сессии
    return redirect(url_for('login'))  # Перенаправление на страницу входа


@app.route('/subject')
def subject_page():
    if session.get('user_role') != 'subject':
        return "Доступ запрещен", 403

    user_id = session.get('user_id')
    user = User.query.get(user_id)

    return render_template('subject.html', user=user)


@app.route('/update_mistakes', methods=['POST'])
def update_mistakes():
    data = request.get_json()
    user_id = data['user_id']
    mistakes = data['mistakes']

    # Обновляем количество ошибок для пользователя в базе данных
    # Пример: db.update_user_mistakes(user_id, mistakes)

    return jsonify({'success': True})


@app.route('/test', methods=['GET', 'POST'])
def test():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    test_session = session.get('test_session')
    if not test_session:
        test_session = {
            'tables': [TestTable(5, 5).get_state() for _ in range(5)],
            'current_table_index': 0,
            'start_time': time.time()
        }
        session['test_session'] = test_session

    current_table_index = test_session['current_table_index']
    table_state = test_session['tables'][current_table_index]
    table = TestTable.from_state(5, 5, table_state)

    if request.method == 'POST':
        number = int(request.json.get('number'))
        is_correct = table.check_number(number)

        if table.is_completed():
            end_time = time.time()
            time_spent = int(end_time - test_session['start_time'])

            # Save table results
            result = TestResult(
                user_id=user_id,
                table_index=current_table_index,
                mistakes=table.mistakes,
                time_spent=timedelta(seconds=time_spent)
            )
            db.session.add(result)
            db.session.commit()

            # Progress to the next table
            if current_table_index < 4:
                test_session['current_table_index'] += 1
                test_session['start_time'] = time.time()
                session['test_session'] = test_session
                return jsonify({"correct": is_correct, "mistakes": table.mistakes, "next_table": True})
            else:
                session.pop('test_session', None)  # End test
                return jsonify({"completed": True})

        # Update session
        test_session['tables'][current_table_index] = table.get_state()
        session['test_session'] = test_session
        return jsonify({"correct": is_correct, "mistakes": table.mistakes})

    time_spent = int(time.time() - test_session['start_time'])
    return render_template(
        'test.html',
        table=table.table,
        table_index=current_table_index,
        mistakes=table.mistakes,
        time_spent=time_spent
    )


@app.route('/result')
def result():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    results = TestResult.query.filter_by(user_id=user_id).order_by(TestResult.table_index).all()

    # Расчет метрик
    total_time = sum(result.time_spent.total_seconds() for result in results)
    times = [result.time_spent.total_seconds() for result in results]

    efficiency = total_time / 5
    workability = times[0] / efficiency
    mental_stability = times[3] / efficiency

    return render_template(
        'result.html',
        results=results,
        efficiency=efficiency,
        workability=workability,
        mental_stability=mental_stability
    )


# Маршрут для страницы психолога
@app.route('/psychologist', methods=['GET', 'POST'])
def psychologist_page():
    if session.get('user_role') != 'psychologist':
        return "Доступ запрещен", 403

    # Получаем всех пользователей с ролью 'subject' и сортируем по ID
    users = User.query.filter_by(role='subject').order_by(User.id).all()

    if request.method == 'POST':
        # Обработка кнопки "Назначить тест"
        if 'user_id' in request.form:
            user_id = int(request.form['user_id'])
            user = User.query.get(user_id)
            if user:
                user.test_assigned = True  # Назначить тест
                db.session.commit()

        # Обработка кнопки "Убрать назначение"
        elif 'remove_assignment' in request.form:
            user_id = int(request.form['remove_assignment'])
            user = User.query.get(user_id)
            if user:
                user.test_assigned = False  # Убираем назначение
                db.session.commit()

    return render_template('psychologist.html', users=users)


# Страница добавления пользователя
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Добавляем нового пользователя в базу
        new_user = User(name=name, email=email, role='user')  # Указываем роль пользователя
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('admin'))  # Перенаправляем на страницу администратора

    return render_template('add_user.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    # Проверка роли пользователя
    if session.get('user_role') != 'admin':
        return "Доступ запрещен", 403

    # Получение всех пользователей из базы данных
    users = User.query.all()

    if request.method == 'POST':
        action = request.form['action']
        if action == 'add':
            name = request.form['name']
            email = request.form['email']
            role = request.form['role']
            # Добавление нового пользователя
            new_user = User(name=name, email=email, role=role)
            db.session.add(new_user)
            db.session.commit()
        elif action == 'delete':
            user_id = int(request.form['user_id'])
            # Удаление пользователя
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()

        # Редирект обратно на страницу администратора для обновления данных
        return redirect(url_for('admin_page'))

    # Отображение страницы с текущими пользователями
    return render_template('admin.html', users=users)


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('login'))

    if user_role == 'admin':
        return redirect(url_for('admin_page'))
    elif user_role == 'psychologist':
        return redirect(url_for('psychologist_page'))
    elif user_role == 'subject':
        return redirect(url_for('subject_page'))
    else:
        return "Неизвестная роль", 403


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            session['user_role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Пользователь не найден")
    return render_template('login.html')


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()  # Удаляет все таблицы
        db.create_all()  # Пересоздаёт таблицы
        # Добавляем администратора, если его нет
        admin_email = "admin@example.com"
        admin_name = "Admin"
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin_user = User(name=admin_name, email=admin_email, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print(f"Администратор {admin_name} добавлен с email {admin_email}")
        else:
            print(f"Администратор уже существует: {existing_admin.name}, email: {existing_admin.email}")

    app.run(debug=True)
