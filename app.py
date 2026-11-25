import os
from flask import Flask, session, g
from config import Config
import models
import validators
from security import generate_csrf_token, validate_csrf_token
from routes.overview import overview_bp
from routes.auth import auth_bp
from routes.students import students_bp
from routes.testing import testing_bp


def create_app(config_class=Config):
    """Application factory for the Student Management & QA Platform."""
    application = Flask(__name__)
    application.config.from_object(config_class)

    with application.app_context():
        models.init_db(application.config['DATABASE'])
        models.ensure_default_admin(application.config['DATABASE'])

    @application.template_filter('calculate_grade')
    def grade_filter(marks):
        return validators.calculate_grade(marks)

    @application.context_processor
    def inject_security_context():
        return dict(csrf_token=generate_csrf_token)

    @application.before_request
    def load_user_and_check_csrf():
        user_id = session.get('user_id')
        if user_id is None:
            g.user = None
        else:
            g.user = models.get_user_by_id(user_id, db_path=application.config['DATABASE'])
            if g.user is None:
                session.clear()
        validate_csrf_token()

    @application.route('/favicon.ico')
    def favicon():
        return ('', 204)

    application.register_blueprint(overview_bp)
    application.register_blueprint(auth_bp)
    application.register_blueprint(students_bp)
    application.register_blueprint(testing_bp)

    return application


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
