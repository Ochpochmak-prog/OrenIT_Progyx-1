# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=64)])
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=64)])
    middle_name = StringField('Отчество', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[Length(min=7, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=5)])
    confirm_password = PasswordField('Подтверждение пароля',
                                     validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать.')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=5)])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class UpdateProfileForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=64)])
    middle_name = StringField('Отчество', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[Length(min=7, max=20)])
    submit = SubmitField('Сохранить изменения')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=5)])
    confirm_new_password = PasswordField('Подтверждение пароля',
                                         validators=[DataRequired(), EqualTo('new_password',
                                         message='Пароли должны совпадать.')])
    submit = SubmitField('Изменить пароль')