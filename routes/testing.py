import io
import csv
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, current_app, g
import models
import test_runner
from security import login_required

testing_bp = Blueprint('testing', __name__)


@testing_bp.route('/testing/dashboard')
@login_required
def testing_dashboard():
    db_path = current_app.config['DATABASE']
    latest_run = models.get_latest_test_run(db_path=db_path)
    recent_runs = models.get_recent_test_runs(limit=6, db_path=db_path)

    test_results = None
    if latest_run and latest_run['results_json']:
        try:
            test_results = json.loads(latest_run['results_json'])
        except Exception:
            test_results = None

    defect_stats = models.get_defect_stats(db_path=db_path)

    return render_template(
        'testing/dashboard.html',
        test_results=test_results,
        latest_run=latest_run,
        recent_runs=recent_runs,
        defect_stats=defect_stats
    )


@testing_bp.route('/testing/run', methods=['POST'])
@login_required
def trigger_automated_tests():
    """
    Executes Pytest and Coverage.py programmatically.
    Supports optional 'suite' parameter (all, bva, ecp, unit, integration, regression, auth).
    """
    db_path = current_app.config['DATABASE']
    suite = request.form.get('suite') or (request.get_json(silent=True) or {}).get('suite') or request.args.get('suite') or 'all'
    results = test_runner.run_tests_and_coverage(db_path=db_path, suite=suite)

    models.log_activity(
        g.user['username'], "TEST_RUN", "TestSuite", suite,
        f"Executed '{suite}' suite: {results['passed']}/{results['total_tests']} passed ({results['coverage']['overall_percent']}% coverage)",
        db_path=db_path
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify(results)

    suite_label = suite.upper() if suite != 'all' else 'Full'
    flash(
        f"Automated test run ({suite_label}) completed: {results['passed']}/{results['total_tests']} passed ({results['coverage']['overall_percent']}% coverage).",
        "success" if results['failed'] == 0 else "warning"
    )
    return redirect(url_for('testing.testing_dashboard'))


@testing_bp.route('/testing/export')
@login_required
def export_test_report_csv():
    db_path = current_app.config['DATABASE']
    latest_run = models.get_latest_test_run(db_path=db_path)
    if not latest_run or not latest_run.get('results_json'):
        flash("No test report available to export. Run automated tests first.", "warning")
        return redirect(url_for('testing.testing_dashboard'))

    results = json.loads(latest_run['results_json'])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Test Case', 'File', 'Technique', 'Status', 'Duration (s)', 'Assertion Message'])
    for idx, tc in enumerate(results.get('test_cases', []), start=1):
        writer.writerow([idx, tc['name'], tc['file'], tc['type'], tc['status'], tc['duration'], tc['message']])

    models.log_activity(g.user['username'], "EXPORT_CSV", "TestReport", latest_run['id'], "Exported automated test report", db_path=db_path)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=automated_test_report.csv'}
    )


@testing_bp.route('/testing/defects')
@login_required
def list_defects():
    db_path = current_app.config['DATABASE']
    status_filter = request.args.get('status', 'All')
    severity_filter = request.args.get('severity', 'All')

    defects = models.get_all_defects(
        status=status_filter,
        severity=severity_filter,
        db_path=db_path
    )
    defect_stats = models.get_defect_stats(db_path=db_path)

    return render_template(
        'testing/defects.html',
        defects=defects,
        defect_stats=defect_stats,
        status_filter=status_filter,
        severity_filter=severity_filter
    )


@testing_bp.route('/testing/defects/<int:id>')
@login_required
def view_defect(id):
    db_path = current_app.config['DATABASE']
    defect = models.get_defect_by_id(id, db_path=db_path)
    if not defect:
        flash("Defect record not found.", "warning")
        return redirect(url_for('testing.list_defects'))
    return render_template('testing/defect_view.html', defect=defect)


@testing_bp.route('/testing/defects/add', methods=['GET', 'POST'])
@login_required
def add_defect():
    db_path = current_app.config['DATABASE']
    if request.method == 'POST':
        bug_id = request.form.get('bug_id', '').strip().upper()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        steps_to_reproduce = request.form.get('steps_to_reproduce', '').strip()
        module = request.form.get('module', '').strip()
        severity = request.form.get('severity', 'Medium').strip()
        status = request.form.get('status', 'Open').strip()
        found_by_test = request.form.get('found_by_test', '').strip()
        resolution_notes = request.form.get('resolution_notes', '').strip()

        preserved = {
            'bug_id': bug_id,
            'title': title,
            'description': description,
            'steps_to_reproduce': steps_to_reproduce,
            'module': module,
            'severity': severity,
            'status': status,
            'found_by_test': found_by_test,
            'resolution_notes': resolution_notes,
        }

        if not bug_id or not title or not description or not module:
            flash("Bug ID, Title, Module, and Description are required fields.", "danger")
            return render_template('testing/defect_form.html', defect=preserved, mode='add')

        try:
            did = models.create_defect(
                bug_id=bug_id,
                title=title,
                description=description,
                steps_to_reproduce=steps_to_reproduce,
                module=module,
                severity=severity,
                status=status,
                found_by_test=found_by_test,
                resolution_notes=resolution_notes,
                db_path=db_path
            )
            models.log_activity(g.user['username'], "CREATE", "Defect", did, f"Logged defect {bug_id}: {title}", db_path=db_path)
            flash(f"Defect {bug_id} logged successfully.", "success")
            return redirect(url_for('testing.list_defects'))
        except Exception as e:
            flash(f"Error logging defect: {str(e)}", "danger")
            return render_template('testing/defect_form.html', defect=preserved, mode='add')

    stats = models.get_defect_stats(db_path=db_path)
    next_bug_id = f"BUG-{100 + stats['total'] + 1}"
    prefill_test = request.args.get('test', '').strip()
    prefill_title = request.args.get('title', '').strip()
    return render_template(
        'testing/defect_form.html',
        defect={'bug_id': next_bug_id, 'found_by_test': prefill_test, 'title': prefill_title},
        mode='add'
    )


@testing_bp.route('/testing/defects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_defect(id):
    db_path = current_app.config['DATABASE']
    defect = models.get_defect_by_id(id, db_path=db_path)
    if not defect:
        flash("Defect record not found.", "warning")
        return redirect(url_for('testing.list_defects'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        steps_to_reproduce = request.form.get('steps_to_reproduce', '').strip()
        module = request.form.get('module', '').strip()
        severity = request.form.get('severity', 'Medium').strip()
        status = request.form.get('status', 'Open').strip()
        resolution_notes = request.form.get('resolution_notes', '').strip()

        if not title or not description or not module:
            flash("Title, Module, and Description are required.", "danger")
            return render_template('testing/defect_form.html', defect=defect, mode='edit')

        models.update_defect(
            defect_id=id,
            title=title,
            description=description,
            steps_to_reproduce=steps_to_reproduce,
            module=module,
            severity=severity,
            status=status,
            resolution_notes=resolution_notes,
            db_path=db_path
        )
        models.log_activity(g.user['username'], "UPDATE", "Defect", id, f"Updated {defect['bug_id']} -> {status}", db_path=db_path)
        flash(f"Defect {defect['bug_id']} updated successfully.", "success")
        return redirect(url_for('testing.list_defects'))

    return render_template('testing/defect_form.html', defect=defect, mode='edit')


@testing_bp.route('/testing/defects/<int:id>/status', methods=['POST'])
@login_required
def transition_defect_status(id):
    db_path = current_app.config['DATABASE']
    defect = models.get_defect_by_id(id, db_path=db_path)
    if not defect:
        flash("Defect record not found.", "warning")
        return redirect(url_for('testing.list_defects'))

    new_status = request.form.get('status', '').strip()
    if new_status not in ('Open', 'In Progress', 'Resolved', 'Closed'):
        flash("Invalid defect status transition.", "danger")
        return redirect(url_for('testing.view_defect', id=id))

    models.update_defect(
        defect_id=id,
        title=defect['title'],
        description=defect['description'],
        steps_to_reproduce=defect['steps_to_reproduce'],
        module=defect['module'],
        severity=defect['severity'],
        status=new_status,
        resolution_notes=defect['resolution_notes'],
        db_path=db_path
    )
    models.log_activity(g.user['username'], "STATUS_CHANGE", "Defect", id, f"{defect['bug_id']}: {defect['status']} -> {new_status}", db_path=db_path)

    if new_status == 'Resolved':
        flash(f"{defect['bug_id']} marked Resolved. Re-run the Regression Suite to verify before closing.", "success")
    else:
        flash(f"{defect['bug_id']} moved to '{new_status}'.", "success")
    return redirect(url_for('testing.view_defect', id=id))


@testing_bp.route('/testing/defects/<int:id>/delete', methods=['POST'])
@login_required
def delete_defect(id):
    db_path = current_app.config['DATABASE']
    defect = models.get_defect_by_id(id, db_path=db_path)
    if defect:
        models.delete_defect(id, db_path=db_path)
        models.log_activity(g.user['username'], "DELETE", "Defect", id, f"Deleted {defect['bug_id']}", db_path=db_path)
        flash(f"Defect {defect['bug_id']} deleted.", "info")
    return redirect(url_for('testing.list_defects'))


@testing_bp.route('/testing/audit')
@login_required
def audit_logs():
    logs = models.get_recent_audit_logs(limit=50, db_path=current_app.config['DATABASE'])
    return render_template('testing/audit.html', logs=logs)


@testing_bp.route('/testing/methodology')
@login_required
def testing_methodology():
    return render_template('testing/methodology.html')
