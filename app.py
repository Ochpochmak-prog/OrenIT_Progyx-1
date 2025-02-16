# app.py
import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, redirect, flash, url_for, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         current_user, login_required)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from card_generator import generate_memorial_card
from flask_migrate import Migrate
from forms import RegistrationForm, LoginForm, UpdateProfileForm, ChangePasswordForm
import random

# --- 1. Настройка соглашения об именовании для ограничений ---
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

# --- 2. Инициализация приложения, конфигурации и базы данных ---
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# --- 3. МОДЕЛИ ---

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='user')
    is_blocked = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return not self.is_blocked


class Record(db.Model):
    __tablename__ = 'record'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.String(20), nullable=True)
    death_date = db.Column(db.String(20), nullable=True)
    photo_path = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    burial_place = db.Column(db.String(200), nullable=True)
    awards = db.Column(db.String(300), nullable=True)
    military_service = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Новое поле для хранения указания конфликта
    conflict = db.Column(db.String(200), nullable=True)

    # Статус заявки (pending, approved, rejected), если вы его используете
    status = db.Column(db.String(20), default='pending')

    def get_awards_list(self):
        if self.awards:
            return [a.strip() for a in self.awards.split(',')]
        return []



class Log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="logs")


# --- 4. UTILS и Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def role_required(roles):
    """Декоратор, ограничивающий доступ по ролям."""
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


def add_log(action):
    """Функция для добавления записи в журнал действий."""
    if current_user.is_authenticated:
        log_entry = Log(user_id=current_user.id, action=action)
        db.session.add(log_entry)
        db.session.commit()


# --- 5. Маршруты публичной части и аутентификации ---

@app.route('/')
def index():
    """
    Если пользователь аутентифицирован как админ — идём в панель админа.
    Если аутентифицирован как user — показываем user_index.html.
    Если не аутентифицирован — показываем guest_index.html.
    """
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            # Покажем страницу user_index.html
            return render_template('user_index.html', user=current_user)
    # Если не аутентифицирован, покажем guest_index.html
    return render_template('guest_index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Считываем данные из формы
        email = form.email.data
        first_name = form.first_name.data
        middle_name = form.middle_name.data
        last_name = form.last_name.data
        phone = form.phone.data
        password = form.password.data

        # Проверяем, не занят ли email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Пользователь с такой почтой уже существует!', 'error')
            return redirect(url_for('register'))

        # Создаём нового пользователя в БД
        new_user = User(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            phone=phone
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # После успешной регистрации, сразу авторизуем пользователя
        login_user(new_user, remember=form.remember_me.data)
        flash("Регистрация прошла успешно! Вы вошли в систему.", "success")

        # Перенаправляем в личный кабинет
        return redirect(url_for('profile'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user:
            if user.is_blocked:
                flash("Ваш аккаунт заблокирован.", "error")
                return redirect(url_for('login'))
            if user.check_password(password):
                login_user(user, remember=form.remember_me.data)
                flash(f"Добро пожаловать, {user.first_name}!", "success")
                return redirect(url_for('index'))
        flash("Неправильная почта или пароль.", "error")
        return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for('index'))


# ============== НЕДОСТАЮЩИЕ МАРШРУТЫ ДЛЯ СУЩЕСТВУЮЩИХ ШАБЛОНОВ ==============

@app.route('/about')
def about():
    """Шаблон about.html — О проекте."""
    return render_template('about.html')


@app.route('/contacts')
def contacts():
    """Шаблон contacts.html — Контакты."""
    return render_template('contacts.html')


@app.route('/faq')
def faq():
    """Шаблон faq.html — Частые вопросы."""
    return render_template('faq.html')


@app.route('/legal_docs')
def legal_docs():
    """Шаблон legal_docs.html — Нормативные документы."""
    return render_template('legal_docs.html')


@app.route('/conflict_filter')
def conflict_filter():
    # Считываем из GET-параметра "q" то, что пользователь ввёл
    query_text = request.args.get('q', '').strip()

    # Стартовый запрос: выбираем записи только со статусом "approved"
    query = Record.query.filter_by(status='approved')

    # Если пользователь ввёл текст, фильтруем по конфликту
    if query_text:
        # Фильтрация по подстроке в поле "conflict" (ILike для нечувствительности к регистру в PostgreSQL / Sqlite)
        query = query.filter(Record.conflict.ilike(f"%{query_text}%"))

    # Выполняем запрос
    records = query.all()

    # Рендерим шаблон "conflict_filter.html", передаём список записей и текст поиска
    return render_template('conflict_filter.html', records=records, query_text=query_text)


@app.route('/municipalities')
def municipalities():
    """Шаблон municipalities.html — Список муниципальных образований."""
    return render_template('municipalities.html')


@app.route('/all_records')
def all_records():
    """Шаблон all_records.html — Все записи."""
    return render_template('all_records.html')


@app.route('/search_by_name')
def search_by_name():
    """Шаблон search_by_name.html — Поиск по фамилии."""
    return render_template('search_by_name.html')


# --- 6. Маршруты административной панели ---

@app.route('/admin')
@role_required(['admin'])
def admin_dashboard():
    return render_template('admin_dashboard.html', user=current_user)


# Управление пользователями
@app.route('/admin/users')
@role_required(['admin'])
def manage_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users, user=current_user)


@app.route('/admin/users/toggle_block/<int:user_id>')
@role_required(['admin'])
def toggle_user_block(user_id):
    if current_user.id == user_id:
        flash("Невозможно заблокировать самого себя.", "warning")
        return redirect(url_for('manage_users'))
    user_to_toggle = User.query.get_or_404(user_id)
    user_to_toggle.is_blocked = not user_to_toggle.is_blocked
    db.session.commit()
    status = "заблокирован" if user_to_toggle.is_blocked else "разблокирован"
    flash(f"Пользователь {user_to_toggle.email} {status}.", "success")
    add_log(f"Пользователь {user_to_toggle.email} {status}")
    return redirect(url_for('manage_users'))


# Управление записями (CRUD)
@app.route('/admin/records')
@role_required(['admin'])
def manage_records():
    records = Record.query.all()
    return render_template('admin_records.html', records=records)


@app.route('/admin/records/approve/<int:record_id>')
@role_required(['admin'])
def approve_record(record_id):
    record = Record.query.get_or_404(record_id)
    if record.status != 'pending':
        flash("Эта запись уже не находится в ожидании!", "warning")
        return redirect(url_for('manage_records'))

    record.status = 'approved'
    db.session.commit()
    flash(f"Запись #{record.id} утверждена!", "success")
    # Можно здесь же вызвать генерацию карточки,
    # если нужно сразу после approve, например:
    # return redirect(url_for('generate_card', record_id=record.id))
    return redirect(url_for('manage_records'))
def generate_card(record_id):
    record = Record.query.get_or_404(record_id)
    data = {
        "full_name": record.full_name,
        "birth_date": record.birth_date,
        "death_date": record.death_date,
        "photo_path": record.photo_path,
        "description": record.description,
        "burial_place": record.burial_place,
        "awards": record.get_awards_list(),
        "military_service": record.military_service,
    }
    cards_folder = os.path.join("static", "cards")
    if not os.path.exists(cards_folder):
        os.makedirs(cards_folder)
    output_filename = f"record_{record_id}.png"
    output_path = os.path.join(cards_folder, output_filename)
    generate_memorial_card(data, output_path)
    flash("Карточка успешно сгенерирована!", "success")
    return redirect(url_for('show_card', filename=output_filename))

@app.route('/admin/records/create', methods=['GET', 'POST'])
@role_required(['admin'])
def create_record():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        birth_date = request.form.get('birth_date')
        death_date = request.form.get('death_date')
        description = request.form.get('description')
        burial_place = request.form.get('burial_place')
        awards = request.form.get('awards')
        military_service = request.form.get('military_service')
        photo_file = request.files.get('photo')

        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join("static", "images", photo_filename)
            photo_file.save(photo_path)
        else:
            photo_path = None

        # При создании админом запись сразу одобряется
        record = Record(full_name=full_name, birth_date=birth_date, death_date=death_date,
                        description=description, burial_place=burial_place, awards=awards,
                        military_service=military_service, photo_path=photo_path, status='approved')
        db.session.add(record)
        db.session.commit()
        flash("Запись успешно создана и одобрена!", "success")
        return redirect(url_for('manage_records'))
    return render_template('admin_record_form.html', action='create')



@app.route('/admin/records/edit/<int:record_id>', methods=['GET', 'POST'])
@role_required(['admin'])
def edit_record(record_id):
    record = Record.query.get_or_404(record_id)
    if request.method == 'POST':
        record.full_name = request.form.get('full_name')
        record.birth_date = request.form.get('birth_date')
        record.death_date = request.form.get('death_date')
        record.description = request.form.get('description')
        record.burial_place = request.form.get('burial_place')
        record.awards = request.form.get('awards')
        record.military_service = request.form.get('military_service')
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join("static", "images", photo_filename)
            photo_file.save(photo_path)
            record.photo_path = photo_path
        db.session.commit()
        flash("Запись обновлена!", "success")
        return redirect(url_for('manage_records'))
    return render_template('admin_record_form.html', action='edit', record=record)


@app.route('/admin/records/delete/<int:record_id>')
@role_required(['admin'])
def delete_record(record_id):
    record = Record.query.get_or_404(record_id)
    title = record.full_name
    db.session.delete(record)
    db.session.commit()
    add_log(f"Удалена запись: {title}")
    flash(f'Запись "{title}" удалена.', "success")
    return redirect(url_for('manage_records'))


# Генерация мемориальной карточки
@app.route('/admin/records/generate_card/<int:record_id>')
@role_required(['admin'])
def generate_card(record_id):
    record = Record.query.get_or_404(record_id)
    data = {
        "full_name": record.full_name,
        "birth_date": record.birth_date,
        "death_date": record.death_date,
        "photo_path": record.photo_path,
        "description": record.description,
        "burial_place": record.burial_place,
        "awards": record.get_awards_list(),
        "military_service": record.military_service,
    }
    cards_folder = os.path.join("static", "cards")
    if not os.path.exists(cards_folder):
        os.makedirs(cards_folder)
    output_filename = f"record_{record_id}.png"
    output_path = os.path.join(cards_folder, output_filename)
    generate_memorial_card(data, output_path)
    flash("Карточка успешно сгенерирована!", "success")
    return redirect(url_for('show_card', filename=output_filename))


@app.route('/admin/records/show_card/<path:filename>')
@role_required(['admin'])
def show_card(filename):
    return render_template('admin_generate_card.html', filename=filename)


# Настройки (демо-страница)
@app.route('/admin/settings', methods=['GET', 'POST'])
@role_required(['admin'])
def admin_settings():
    if request.method == 'POST':
        site_title = request.form.get('site_title')
        flash(f'Настройки сохранены! (site_title={site_title})', "success")
        add_log("Изменены настройки сайта")
        return redirect(url_for('admin_settings'))
    return render_template('admin_settings.html')


# Журнал действий
@app.route('/admin/logs')
@role_required(['admin'])
def view_logs():
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    return render_template('admin_logs.html', logs=logs)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    update_form = UpdateProfileForm()
    pass_form = ChangePasswordForm()

    if update_form.validate_on_submit():
        # Проверка уникальности email и обновление полей:
        if update_form.email.data != current_user.email:
            email_exists = User.query.filter_by(email=update_form.email.data).first()
            if email_exists and email_exists.id != current_user.id:
                flash("Данный email уже используется другим аккаунтом!", "error")
                return redirect(url_for('profile'))

        current_user.first_name = update_form.first_name.data
        current_user.middle_name = update_form.middle_name.data
        current_user.last_name = update_form.last_name.data
        current_user.email = update_form.email.data
        current_user.phone = update_form.phone.data
        db.session.commit()

        flash("Профиль обновлён!", "success")
        return redirect(url_for('profile'))

    return render_template(
        'user_profile.html',
        user=current_user,
        update_form=update_form,
        pass_form=pass_form
    )

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    pass_form = ChangePasswordForm()
    if pass_form.validate_on_submit():
        current_password = pass_form.current_password.data
        new_password = pass_form.new_password.data

        # Проверяем, верен ли текущий пароль
        if not current_user.check_password(current_password):
            flash("Текущий пароль неверен!", "error")
            return redirect(url_for('profile'))

        # Если верен, ставим новый
        current_user.set_password(new_password)
        db.session.commit()
        flash("Пароль успешно изменён!", "success")
        return redirect(url_for('profile'))

    # Если форма не прошла валидацию, вернёмся в профиль
    # и отрисуем ошибки (т.к. мы туда передаём эту же форму).
    flash("Ошибка при изменении пароля.", "error")
    return redirect(url_for('profile'))

@app.route('/user/records/new', methods=['GET', 'POST'])
@login_required
def create_user_record():
    if current_user.role != 'user':
        flash("Недоступно для вашей роли!", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        birth_date = request.form.get('birth_date')
        death_date = request.form.get('death_date')
        description = request.form.get('description')
        burial_place = request.form.get('burial_place')
        awards = request.form.get('awards')
        military_service = request.form.get('military_service')
        photo_file = request.files.get('photo')

        # Обрабатываем загрузку файла
        photo_path = None
        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join("static", "images", photo_filename)
            photo_file.save(photo_path)

        # Создаём запись со статусом "pending"
        record = Record(
            full_name=full_name,
            birth_date=birth_date,
            death_date=death_date,
            description=description,
            burial_place=burial_place,
            awards=awards,
            military_service=military_service,
            photo_path=photo_path,
            status="pending"
        )
        db.session.add(record)
        db.session.commit()

        flash("Заявка на создание карточки отправлена и ожидает подтверждения администратора!", "success")
        return redirect(url_for('index'))

    return render_template('user_record_form.html')


@app.route('/map_view')
def map_view():
    # Выбираем одобренные записи
    approved = Record.query.filter_by(status='approved').all()
    left_card = None
    right_card = None
    if approved:
        random.shuffle(approved)
        left_card = approved[0]  # первая случайная карточка
        if len(approved) > 1:
            right_card = approved[1]  # вторая случайная карточка
    # Если вам нужен идентификатор слоя, убедитесь, что он задан в Config, или уберите этот параметр
    return render_template('map.html', left_card=left_card, right_card=right_card, map_layer_id=getattr(Config, 'LAYER_ID_MAP', None))

@app.route('/cards/search')
def search_cards():
    name_query = request.args.get('name', '').strip()
    conflict_query = request.args.get('conflict', '').strip()

    # Базовый запрос — только одобренные
    query = Record.query.filter_by(status='approved')

    if name_query:
        # Ищем записи, где full_name LIKE '%name_query%'
        query = query.filter(Record.full_name.ilike(f"%{name_query}%"))

    if conflict_query:
        query = query.filter(Record.conflict.ilike(f"%{conflict_query}%"))

    results = query.all()

    return render_template('search_results.html', results=results,
                           name_query=name_query,
                           conflict_query=conflict_query)

@app.route('/random_cards')
def random_cards():
    # Получаем все одобренные записи
    approved = Record.query.filter_by(status='approved').all()
    # Перемешиваем записи случайным образом
    random.shuffle(approved)
    # Ограничиваем выбор до 2 карточек
    cards = approved[:2]
    return render_template('random_cards.html', cards=cards)

@app.route('/card/<int:record_id>')
def card_detail(record_id):
    record = Record.query.get_or_404(record_id)
    return render_template('card_detail.html', record=record)


# --- 7. MAIN ---
if __name__ == '__main__':
    with app.app_context():
        # db.create_all()  # Только если не используете Flask-Migrate
        # Создание суперпользователя при отсутствии
        super_email = "admin@mail.com"
        admin_user = User.query.filter_by(email=super_email).first()
        if not admin_user:
            admin_user = User(first_name="Super", middle_name="Admin", last_name="User",
                              email=super_email, role="admin")
            admin_user.set_password("adminpass")
            db.session.add(admin_user)
            db.session.commit()
            print("Суперпользователь создан!")
        else:
            print("Суперпользователь уже существует")
    app.run(debug=True)
