import io
import csv
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, current_app, g
import models
import validators
from security import login_required

students_bp = Blueprint('students', __name__)


@students_bp.route('/students')
@login_required
def list_students():
    search_query = request.args.get('search', '').strip()
    selected_dept = request.args.get('department', 'All').strip()
    sort_by = request.args.get('sort', 'id').strip()
    sort_dir = request.args.get('dir', 'desc').strip()
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    per_page = 10

    db_path = current_app.config['DATABASE']
    students, total_matching = models.get_students_paginated(
        search_query=search_query,
        department=selected_dept,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        per_page=per_page,
        db_path=db_path
    )

    total_pages = max(1, math.ceil(total_matching / per_page))
    if page > total_pages:
        page = total_pages

    all_students = models.get_all_students(db_path=db_path)
    total_students = len(all_students)
    avg_marks = 0.0
    pass_count = 0
    fail_count = 0
    if total_students > 0:
        marks_list = [s['marks'] for s in all_students]
        avg_marks = round(sum(marks_list) / total_students, 1)
        pass_count = sum(1 for m in marks_list if m >= 50.0)
        fail_count = total_students - pass_count

    return render_template(
        'students/index.html',
        students=students,
        search_query=search_query,
        selected_dept=selected_dept,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        total_pages=total_pages,
        total_matching=total_matching,
        departments=validators.VALID_DEPARTMENTS,
        total_students=total_students,
        avg_marks=avg_marks,
        pass_count=pass_count,
        fail_count=fail_count
    )


@students_bp.route('/students/export')
@login_required
def export_students_csv():
    search_query = request.args.get('search', '').strip()
    selected_dept = request.args.get('department', 'All').strip()
    db_path = current_app.config['DATABASE']
    students = models.get_all_students(
        search_query=search_query,
        department=selected_dept,
        db_path=db_path
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Register Number', 'Name', 'Department', 'Email', 'Marks', 'Grade', 'Status'])
    for s in students:
        grade = validators.calculate_grade(s['marks'])
        status = 'Pass' if s['marks'] >= 50.0 else 'Fail'
        writer.writerow([s['register_number'], s['name'], s['department'], s['email'], f"{s['marks']:.2f}", grade, status])

    models.log_activity(g.user['username'], "EXPORT_CSV", "Student", None, f"Exported {len(students)} student records", db_path=db_path)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=student_records.csv'}
    )


@students_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    errors = {}
    form_data = {
        'register_number': '',
        'name': '',
        'department': '',
        'email': '',
        'marks': ''
    }

    if request.method == 'POST':
        form_data = {
            'register_number': request.form.get('register_number', '').strip(),
            'name': request.form.get('name', '').strip(),
            'department': request.form.get('department', '').strip(),
            'email': request.form.get('email', '').strip(),
            'marks': request.form.get('marks', '').strip()
        }

        db_path = current_app.config['DATABASE']
        db_conn = models.get_db_connection(db_path)
        try:
            is_valid, errors, cleaned = validators.validate_student(
                form_data, existing_student_id=None, db=db_conn
            )
        finally:
            db_conn.close()

        if is_valid:
            try:
                sid = models.create_student(
                    register_number=cleaned['register_number'],
                    name=cleaned['name'],
                    department=cleaned['department'],
                    email=cleaned['email'],
                    marks=cleaned['marks'],
                    db_path=db_path
                )
                models.log_activity(
                    g.user['username'], "CREATE", "Student", sid,
                    f"Added {cleaned['register_number']} ({cleaned['name']})", db_path=db_path
                )
                flash(f"Student '{cleaned['name']}' (Reg: {cleaned['register_number']}) added successfully.", "success")
                return redirect(url_for('students.list_students'))
            except Exception as e:
                flash(f"Database error: {str(e)}", "danger")
        else:
            flash("Please correct the validation errors highlighted below.", "danger")

    return render_template(
        'students/add.html',
        errors=errors,
        form_data=form_data,
        departments=validators.VALID_DEPARTMENTS
    )


@students_bp.route('/students/<int:id>')
@login_required
def view_student(id):
    db_path = current_app.config['DATABASE']
    student = models.get_student_by_id(id, db_path=db_path)
    if not student:
        flash("Student record not found.", "warning")
        return redirect(url_for('students.list_students'))

    grade = validators.calculate_grade(student['marks'])
    return render_template('students/view.html', student=student, grade=grade)


@students_bp.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    db_path = current_app.config['DATABASE']
    student = models.get_student_by_id(id, db_path=db_path)
    if not student:
        flash("Student record not found.", "warning")
        return redirect(url_for('students.list_students'))

    errors = {}
    form_data = {
        'register_number': student['register_number'],
        'name': student['name'],
        'department': student['department'],
        'email': student['email'],
        'marks': str(student['marks'])
    }

    if request.method == 'POST':
        form_data = {
            'register_number': request.form.get('register_number', '').strip(),
            'name': request.form.get('name', '').strip(),
            'department': request.form.get('department', '').strip(),
            'email': request.form.get('email', '').strip(),
            'marks': request.form.get('marks', '').strip()
        }

        db_conn = models.get_db_connection(db_path)
        try:
            is_valid, errors, cleaned = validators.validate_student(
                form_data, existing_student_id=id, db=db_conn
            )
        finally:
            db_conn.close()

        if is_valid:
            try:
                models.update_student(
                    student_id=id,
                    register_number=cleaned['register_number'],
                    name=cleaned['name'],
                    department=cleaned['department'],
                    email=cleaned['email'],
                    marks=cleaned['marks'],
                    db_path=db_path
                )
                models.log_activity(
                    g.user['username'], "UPDATE", "Student", id,
                    f"Updated {cleaned['register_number']} ({cleaned['name']})", db_path=db_path
                )
                flash(f"Student record '{cleaned['register_number']}' updated successfully.", "success")
                return redirect(url_for('students.list_students'))
            except Exception as e:
                flash(f"Database error: {str(e)}", "danger")
        else:
            flash("Please correct the validation errors highlighted below.", "danger")

    return render_template(
        'students/edit.html',
        student=student,
        errors=errors,
        form_data=form_data,
        departments=validators.VALID_DEPARTMENTS
    )


@students_bp.route('/students/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    db_path = current_app.config['DATABASE']
    student = models.get_student_by_id(id, db_path=db_path)
    if student:
        models.delete_student(id, db_path=db_path)
        models.log_activity(
            g.user['username'], "DELETE", "Student", id,
            f"Deleted {student['register_number']} ({student['name']})", db_path=db_path
        )
        flash(f"Student record '{student['register_number']}' ({student['name']}) has been deleted.", "info")
    else:
        flash("Student record not found.", "warning")
    return redirect(url_for('students.list_students'))
