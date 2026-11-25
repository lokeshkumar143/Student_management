import json
from flask import Blueprint, render_template, redirect, url_for, current_app, g
import models
from security import login_required

overview_bp = Blueprint('overview', __name__)


@overview_bp.route('/')
def index():
    if g.user is not None:
        return redirect(url_for('overview.home'))
    return redirect(url_for('auth.login'))


@overview_bp.route('/overview')
@login_required
def home():
    db_path = current_app.config['DATABASE']
    all_students = models.get_all_students(db_path=db_path)
    total_students = len(all_students)
    avg_marks = round(sum(s['marks'] for s in all_students) / total_students, 1) if total_students > 0 else 0.0
    pass_count = sum(1 for s in all_students if s['marks'] >= 50.0)

    latest_run = models.get_latest_test_run(db_path=db_path)
    test_summary = None
    if latest_run and latest_run.get('results_json'):
        try:
            test_summary = json.loads(latest_run['results_json'])
        except Exception:
            test_summary = None

    defect_stats = models.get_defect_stats(db_path=db_path)
    recent_logs = models.get_recent_audit_logs(limit=6, db_path=db_path)

    return render_template(
        'overview.html',
        total_students=total_students,
        avg_marks=avg_marks,
        pass_count=pass_count,
        latest_run=latest_run,
        test_summary=test_summary,
        defect_stats=defect_stats,
        recent_logs=recent_logs
    )
