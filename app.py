import os
from functools import wraps
from flask import Flask, render_template, redirect, flash, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         current_user, login_required)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from forms import RegistrationForm, LoginForm
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Инициализация миграций
migrate = Migrate(app, db)

# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128))
    # Роль: 'user' или 'admin'
    role = db.Column(db.String(20), nullable=False, default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Декоратор для ограничения доступа по ролям
def role_required(roles):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Пожалуйста, авторизуйтесь.", "warning")
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash("У вас нет доступа к этой странице.", "danger")
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return decorated_view
    return decorator

# Главная страница: отображение разного контента в зависимости от роли
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return render_template('admin_index.html', user=current_user)
        else:
            return render_template('user_index.html', user=current_user)
    else:
        return render_template('guest_index.html')

# Регистрация нового пользователя (получает роль 'user')
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с такой почтой уже зарегистрирован!', 'error')
            return redirect(url_for('register'))
        new_user = User(
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            role='user'
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Вход в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'Добро пожаловать, {user.first_name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильная почта или пароль.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Дополнительные страницы (общедоступные)
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/map_view')
def map_view():
    return render_template('map.html')

@app.route('/legal_docs')
def legal_docs():
    return render_template('legal_docs.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/all_records')
def all_records():
    return render_template('all_records.html')

@app.route('/municipalities')
def municipalities():
    return render_template('municipalities.html')

@app.route('/conflict_filter')
def conflict_filter():
    return render_template('conflict_filter.html')

# Страница панели администратора (только для admin)
@app.route('/admin')
@role_required(['admin'])
def admin_dashboard():
    return render_template('admin_dashboard.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        # Если вы используете миграции, то не вызывайте db.create_all()
        # Проверяем наличие суперпользователя с заданным email
        super_email = "admin@mail.com"
        admin = User.query.filter_by(email=super_email).first()
        if not admin:
            admin = User(
                first_name="Super",
                middle_name="Admin",
                last_name="User",
                email=super_email,
                phone="",
                role="admin"
            )
            admin.set_password("adminpass")  # Задайте надежный пароль для продакшена
            db.session.add(admin)
            db.session.commit()
            print("Суперпользователь создан!")
        else:
            print("Суперпользователь уже существует")
    app.run(debug=True)
