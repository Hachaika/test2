from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length


class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    role = SelectField('Роль', choices=[('admin', 'Администратор'), ('psychologist', 'Психолог'),
                                        ('subject', 'Испытуемый')], validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать')


class AssignTestForm(FlaskForm):
    test_id = SelectField('Тест', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Испытуемый', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Назначить тест')


class TakeTestForm(FlaskForm):
    responses = StringField('Ответы', validators=[DataRequired()])
    submit = SubmitField('Отправить')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

