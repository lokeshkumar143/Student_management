import pytest
import validators
import models


class TestAuthenticationUnit:
    """
    Unit tests for administrator authentication validators (BVA, ECP, Security).
    """

    def test_validate_username_valid(self):
        ok, res = validators.validate_username("qa_admin.01")
        assert ok is True
        assert res == "qa_admin.01"

    def test_validate_username_bva_lengths(self):
        # Min - 1 (2 chars)
        ok, msg = validators.validate_username("ad")
        assert ok is False
        assert "between 3 and 20" in msg

        # Min (3 chars)
        ok, res = validators.validate_username("adm")
        assert ok is True

        # Max (20 chars)
        ok, res = validators.validate_username("a" * 20)
        assert ok is True

        # Max + 1 (21 chars)
        ok, msg = validators.validate_username("a" * 21)
        assert ok is False
        assert "between 3 and 20" in msg

    def test_validate_username_invalid_chars_and_empty(self):
        assert validators.validate_username("")[0] is False
        assert validators.validate_username(None)[0] is False
        assert validators.validate_username("bad user!")[0] is False

    def test_validate_password_bva_and_complexity(self):
        # Empty / None
        assert validators.validate_password("")[0] is False
        assert validators.validate_password(None)[0] is False

        # Min - 1 (5 chars)
        ok, msg = validators.validate_password("Abc12")
        assert ok is False
        assert "between 6 and 64" in msg

        # Min (6 chars, letter + digit)
        ok, res = validators.validate_password("Abc123")
        assert ok is True

        # Max + 1 (65 chars)
        assert validators.validate_password("A1" + "a" * 63)[0] is False

        # Complexity ECP: letters only / digits only
        ok_letters, msg_letters = validators.validate_password("onlyletters")
        assert ok_letters is False
        assert "letter and one number" in msg_letters

        ok_digits, msg_digits = validators.validate_password("12345678")
        assert ok_digits is False
        assert "letter and one number" in msg_digits

    def test_validate_registration_duplicate_username_and_email(self, temp_db):
        models.create_user("admin", "Admin User", "admin@eduquality.edu", "Admin@123", db_path=temp_db)
        conn = models.get_db_connection(temp_db)
        try:
            ok, errors, _ = validators.validate_registration({
                "username": "ADMIN",
                "full_name": "Another Admin",
                "email": "admin@eduquality.edu",
                "password": "Password1",
                "confirm_password": "Password2"
            }, db=conn)
            assert ok is False
            assert "username" in errors
            assert "email" in errors
        finally:
            conn.close()


class TestAuthenticationIntegration:
    """
    Integration tests for login, logout, registration, and route protection.
    """

    def test_unauthenticated_root_redirects_to_login(self, client):
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_protected_routes_require_login(self, client):
        protected = [
            '/overview',
            '/students',
            '/students/add',
            '/testing/dashboard',
            '/testing/defects',
            '/testing/methodology',
        ]
        for path in protected:
            resp = client.get(path)
            assert resp.status_code == 302
            assert '/login' in resp.headers['Location']

    def test_unauthenticated_ajax_test_run_returns_401(self, client):
        resp = client.post('/testing/run', headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 401

    def test_login_page_renders(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b"Administrator Sign In" in resp.data

    def test_login_valid_credentials(self, client):
        resp = client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Welcome back" in resp.data
        assert b"Operations &amp; QA Workflow" in resp.data

    def test_login_invalid_credentials_rejected(self, client):
        resp = client.post('/login', data={'username': 'admin', 'password': 'WrongPassword'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_login_empty_fields_rejected(self, client):
        resp = client.post('/login', data={'username': '', 'password': ''}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Username is required" in resp.data
        assert b"Password is required" in resp.data

    def test_login_unsafe_next_redirect_blocked(self, client):
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'Admin@123',
            'next': 'https://evil.example.com'
        })
        assert resp.status_code == 302
        assert 'evil.example.com' not in resp.headers['Location']
        assert '/overview' in resp.headers['Location']

    def test_register_new_administrator_and_logout(self, client, temp_db):
        resp_get = client.get('/register')
        assert resp_get.status_code == 200
        assert b"Create Administrator Account" in resp_get.data

        resp_post = client.post('/register', data={
            'username': 'qa_lead',
            'full_name': 'Priya Nair',
            'email': 'priya.nair@eduquality.edu',
            'password': 'QaLead@2026',
            'confirm_password': 'QaLead@2026'
        }, follow_redirects=True)
        assert resp_post.status_code == 200
        assert b"created and signed in" in resp_post.data

        user = models.get_user_by_username('qa_lead', db_path=temp_db)
        assert user is not None

        # Logout
        resp_out = client.post('/logout', follow_redirects=True)
        assert resp_out.status_code == 200
        assert b"Signed out" in resp_out.data
        assert b"Administrator Sign In" in resp_out.data

    def test_profile_and_password_change(self, auth_client, temp_db):
        resp = auth_client.get('/profile')
        assert resp.status_code == 200
        assert b"Update Password" in resp.data

        # Wrong current password rejected
        resp_bad = auth_client.post('/profile', data={
            'current_password': 'WrongPassword1',
            'new_password': 'NewPass@123',
            'confirm_password': 'NewPass@123'
        }, follow_redirects=True)
        assert resp_bad.status_code == 200
        assert b"Current password is incorrect" in resp_bad.data

        # Valid password change succeeds
        resp_ok = auth_client.post('/profile', data={
            'current_password': 'Admin@123',
            'new_password': 'NewPass@123',
            'confirm_password': 'NewPass@123'
        }, follow_redirects=True)
        assert resp_ok.status_code == 200
        assert b"updated successfully" in resp_ok.data
        assert models.verify_user_credentials('admin', 'NewPass@123', db_path=temp_db) is not None

    def test_csrf_protection_enforced_when_enabled(self, temp_db):
        from app import create_app
        from config import Config

        class CsrfTestConfig(Config):
            DATABASE = temp_db
            TESTING = True
            WTF_CSRF_ENABLED = True

        models.ensure_default_admin(temp_db)
        csrf_app = create_app(CsrfTestConfig)
        with csrf_app.test_client() as c:
            # POST without csrf_token fails with 400
            resp_400 = c.post('/login', data={'username': 'admin', 'password': 'Admin@123'})
            assert resp_400.status_code == 400

            # GET login to establish session CSRF token, then POST with valid token
            login_page = c.get('/login')
            assert login_page.status_code == 200
            with c.session_transaction() as sess:
                token = sess.get('_csrf_token')
            assert token is not None

            resp_ok = c.post('/login', data={
                'csrf_token': token,
                'username': 'admin',
                'password': 'Admin@123'
            }, follow_redirects=True)
            assert resp_ok.status_code == 200
            assert b"Welcome back" in resp_ok.data
