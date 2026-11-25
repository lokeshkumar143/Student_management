from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, current_app
import models
import validators
from security import login_required, is_safe_redirect_url

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None:
        return redirect(url_for('overview.home'))

    errors = {}
    username_val = ''
    next_url = request.args.get('next') or request.form.get('next') or ''

    if request.method == 'POST':
        username_val = request.form.get('username', '').strip()
        password_val = request.form.get('password', '')

        if not username_val:
            errors['username'] = "Username is required."
        if not password_val:
            errors['password'] = "Password is required."

        if not errors:
            db_path = current_app.config['DATABASE']
            user = models.verify_user_credentials(username_val, password_val, db_path=db_path)
            if user:
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['role'] = user['role']
                models.update_last_login(user['id'], db_path=db_path)
                models.log_activity(user['username'], "LOGIN", "User", user['id'], "Administrator signed in", db_path=db_path)
                flash(f"Welcome back, {user['full_name']}.", "success")
                if is_safe_redirect_url(next_url):
                    return redirect(next_url)
                return redirect(url_for('overview.home'))
            else:
                errors['auth'] = "Invalid username or password. Please verify your credentials."
                models.log_activity(username_val or "unknown", "LOGIN_FAILED", "User", None, "Invalid credentials attempt", db_path=db_path)
                flash("Invalid username or password.", "danger")

    return render_template('auth/login.html', errors=errors, username=username_val, next_url=next_url)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user is not None:
        return redirect(url_for('overview.home'))

    errors = {}
    form_data = {'username': '', 'full_name': '', 'email': ''}

    if request.method == 'POST':
        form_data = {
            'username': request.form.get('username', '').strip(),
            'full_name': request.form.get('full_name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', '')
        }

        db_path = current_app.config['DATABASE']
        db_conn = models.get_db_connection(db_path)
        try:
            is_valid, errors, cleaned = validators.validate_registration(form_data, db=db_conn)
        finally:
            db_conn.close()

        if is_valid:
            try:
                user_id = models.create_user(
                    username=cleaned['username'],
                    full_name=cleaned['full_name'],
                    email=cleaned['email'],
                    password=cleaned['password'],
                    role='Administrator',
                    db_path=db_path
                )
                session.clear()
                session['user_id'] = user_id
                session['username'] = cleaned['username']
                session['full_name'] = cleaned['full_name']
                session['role'] = 'Administrator'
                models.update_last_login(user_id, db_path=db_path)
                models.log_activity(cleaned['username'], "REGISTER", "User", user_id, "New administrator registered", db_path=db_path)
                flash(f"Account '{cleaned['username']}' created and signed in.", "success")
                return redirect(url_for('overview.home'))
            except Exception as e:
                flash(f"Registration failed: {str(e)}", "danger")
        else:
            flash("Please correct the highlighted errors in your registration form.", "danger")

    return render_template('auth/register.html', errors=errors, form_data=form_data)


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    username = session.get('username')
    if username:
        models.log_activity(username, "LOGOUT", "User", session.get('user_id'), "Administrator signed out", db_path=current_app.config['DATABASE'])
    session.clear()
    if username:
        flash(f"Signed out ({username}).", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    errors = {}
    db_path = current_app.config['DATABASE']

    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        ok, errors = validators.validate_password_change(
            current_pw, new_pw, confirm_pw, g.user['password']
        )
        if ok:
            models.update_user_password(g.user['id'], new_pw, db_path=db_path)
            models.log_activity(g.user['username'], "PASSWORD_UPDATED", "User", g.user['id'], "Administrator changed password", db_path=db_path)
            flash("Your password has been updated successfully.", "success")
            return redirect(url_for('auth.profile'))
        else:
            flash("Please resolve the password validation errors below.", "danger")

    return render_template('auth/profile.html', user=g.user, errors=errors)
