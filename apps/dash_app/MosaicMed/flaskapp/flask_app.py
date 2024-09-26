# flask_app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from services.MosaicMed.flaskapp.file_loader import file_loader_bp
from services.MosaicMed.flaskapp.models import User  # Корректный путь к модели User
from datetime import timedelta

flask_app = Flask(__name__)
flask_app.secret_key = 'your_super_secret_key_xfgh34xfggvi/.gyuhi456'

# Настройки времени жизни сессии
flask_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
flask_app.config['SESSION_PROTECTION'] = 'strong'

login_manager = LoginManager()
login_manager.init_app(flask_app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@flask_app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/main')
    else:
        return redirect('/login')


@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.validate(username, password)
        if user:
            login_user(user)
            return redirect('/')
        else:
            error = 'Ошибка входа. Проверьте правильность введенных данных'
    return render_template('login.html', error=error)


@flask_app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


flask_app.register_blueprint(file_loader_bp)
