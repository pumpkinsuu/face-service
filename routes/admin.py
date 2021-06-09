from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

from database.admin import AdminData
from config.admin import *


def create_admin_bp(app):
    admin_bp = Blueprint('admin_bp', __name__,
                         template_folder='../templates',
                         static_folder='../static')

    db = AdminData(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin_bp.login'

    @login_manager.user_loader
    def load_user(user_id):
        if user_id == USERNAME:
            return User(user_id)
        return None

    class User(UserMixin):
        def __init__(self, user_id):
            self.id = user_id

        def get(self):
            return self.id

    @admin_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if username == USERNAME and password == PASSWORD:
                user = User(USERNAME)
                login_user(user)

                _next = request.args.get('next')
                if _next:
                    return redirect(url_for(_next))
                return redirect(url_for('admin_bp.main'))
            flash('Invalid username or password', 'warn')

        return render_template('loginPage.html')

    @admin_bp.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('admin_bp.login'))

    @admin_bp.route('/')
    @login_required
    def main():
        data = db.get()
        return render_template('mainPage.html', data=data)

    @admin_bp.route('/collection', methods=['GET', 'POST'])
    @login_required
    def create():
        if request.method == 'POST':
            collection = request.form.get('collection')
            if db.get_data(collection):
                flash('Collection exist!', 'warn')
            elif db.create(collection):
                flash('Created', 'info')
                return redirect(url_for('admin_bp.update', collection=collection))
            else:
                flash('Failed to create', 'error')
        return render_template('addPage.html')

    @admin_bp.route('/collection/<collection>', methods=['GET', 'POST'])
    @login_required
    def update(collection):
        if request.method == 'POST':
            if db.update(collection):
                flash('Updated', 'info')
            else:
                flash('Failed to update', 'error')

        data = db.get_data({'collection': collection})
        if not data:
            abort(404)
        return render_template('editPage.html', data=data)

    @admin_bp.route('/collection/<collection>/remove', methods=['POST'])
    @login_required
    def remove(collection):
        if db.remove(collection):
            flash('Removed', 'info')
            return redirect(url_for('admin_bp.main'))
        else:
            flash('Failed to remove', 'error')
            return redirect(url_for('admin_bp.update', collection=collection))

    return admin_bp
