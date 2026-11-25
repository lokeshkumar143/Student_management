import hmac
import secrets
from functools import wraps
from urllib.parse import urlparse
from flask import session, request, redirect, url_for, flash, jsonify, g, current_app, abort


def generate_csrf_token():
    """Generates or returns the active per-session CSRF token."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return session['_csrf_token']


def validate_csrf_token():
    """Validates CSRF token on mutating HTTP requests when CSRF protection is enabled."""
    if not current_app.config.get('WTF_CSRF_ENABLED', True):
        return
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        session_token = session.get('_csrf_token')
        submitted_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not session_token or not submitted_token or not hmac.compare_digest(session_token, submitted_token):
            abort(400, description="Invalid or missing CSRF security token.")


def login_required(view):
    """Protects routes from unauthenticated access."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({"error": "Authentication required."}), 401
            flash("Please sign in with an administrator account to continue.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def is_safe_redirect_url(target):
    """Prevents open redirect vulnerabilities by permitting relative local paths only."""
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == '' and parsed.netloc == '' and target.startswith('/')
