from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

class RegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[
        DataRequired(message='Поле обязательно')
    ])
    first_name = StringField('Имя', validators=[
        DataRequired(message='Поле обязательно')
    ])
    middle_name = StringField('Отчество', validators=[
        DataRequired(message='Поле обязательно')
    ])
    email = StringField('Электронная почта', validators=[
        DataRequired(message='Поле обязательно'),
        Email(message='Неверный формат почты')
    ])
    phone = StringField('Телефон', validators=[
        DataRequired(message='Поле обязательно'),
        Regexp(r'^\+?\d{10,15}$', message='Номер должен содержать от 10 до 15 цифр (возможно с +)')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно'),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(message='Поле обязательно'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Электронная почта', validators=[
        DataRequired(message='Поле обязательно'),
        Email(message='Неверный формат почты')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
