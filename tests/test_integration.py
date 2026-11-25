import pytest
import json
import models


class TestIntegrationRoutes:
    """
    Integration tests covering complete authenticated HTTP request-response workflows.
    """

    def test_home_redirects_to_overview_when_authenticated(self, auth_client):
        resp = auth_client.get('/')
        assert resp.status_code == 302
        assert '/overview' in resp.headers['Location']

        resp_overview = auth_client.get('/overview')
        assert resp_overview.status_code == 200
        assert b"Operations &amp; QA Workflow" in resp_overview.data

    def test_list_students_empty_state(self, auth_client):
        resp = auth_client.get('/students')
        assert resp.status_code == 200
        assert b"No student records found" in resp.data

    def test_add_student_valid_submission(self, auth_client, temp_db):
        payload = {
            'register_number': '192210378',
            'name': 'Katherine Johnson',
            'department': 'Data Science',
            'email': 'katherine@nasa.gov',
            'marks': '99.5'
        }
        resp = auth_client.post('/students/add', data=payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Katherine Johnson" in resp.data
        assert b"192210378" in resp.data
        assert b"added successfully" in resp.data

        student = models.get_student_by_reg_no('192210378', db_path=temp_db)
        assert student is not None
        assert student['marks'] == 99.5

    def test_add_student_boundary_reject_negative_marks(self, auth_client):
        """PDF Requirement Example: 'If user enters -5 or 105, system should display validation error'"""
        payload = {
            'register_number': '192210502',
            'name': 'Invalid Marks Test',
            'department': 'Computer Science',
            'email': 'invalid@test.com',
            'marks': '-5'
        }
        resp = auth_client.post('/students/add', data=payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Marks must be between 0 and 100" in resp.data

    def test_add_student_boundary_reject_exceed_100_marks(self, auth_client):
        """PDF Requirement Example: 'If user enters -5 or 105, system should display validation error'"""
        payload = {
            'register_number': '192210503',
            'name': 'Excessive Marks Test',
            'department': 'Information Technology',
            'email': 'excess@test.com',
            'marks': '105'
        }
        resp = auth_client.post('/students/add', data=payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Marks must be between 0 and 100" in resp.data

    def test_add_student_duplicate_register_number_rejected(self, auth_client):
        """PDF Requirement Example: 'An automated test checks whether the system rejects a duplicate student register number.'"""
        payload1 = {
            'register_number': '192210504',
            'name': 'Original Student',
            'department': 'Computer Science',
            'email': 'orig@test.com',
            'marks': '85'
        }
        auth_client.post('/students/add', data=payload1, follow_redirects=True)

        payload2 = {
            'register_number': '192210504',
            'name': 'Imposter Student',
            'department': 'Data Science',
            'email': 'imposter@test.com',
            'marks': '90'
        }
        resp = auth_client.post('/students/add', data=payload2, follow_redirects=True)
        assert resp.status_code == 200
        assert b"already exists" in resp.data

    def test_view_student_details(self, auth_client, temp_db):
        sid = models.create_student("192210505", "Alan Kay", "Computer Science", "alan@kay.org", 88.0, db_path=temp_db)
        resp = auth_client.get(f'/students/{sid}')
        assert resp.status_code == 200
        assert b"Alan Kay" in resp.data
        assert b"192210505" in resp.data

    def test_edit_student_workflow(self, auth_client, temp_db):
        sid = models.create_student("192210506", "Margaret Hamilton", "Computer Science", "margaret@mit.edu", 92.0, db_path=temp_db)

        edit_payload = {
            'register_number': '192210506',
            'name': 'Margaret Hamilton Apollo',
            'department': 'Computer Science',
            'email': 'margaret.apollo@mit.edu',
            'marks': '98.0'
        }
        resp = auth_client.post(f'/students/{sid}/edit', data=edit_payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"updated successfully" in resp.data

        updated = models.get_student_by_id(sid, db_path=temp_db)
        assert updated['name'] == 'Margaret Hamilton Apollo'
        assert updated['marks'] == 98.0

    def test_delete_student_workflow(self, auth_client, temp_db):
        sid = models.create_student("192210507", "Delete Me", "Civil Engineering", "delete@test.com", 65.0, db_path=temp_db)
        resp = auth_client.post(f'/students/{sid}/delete', follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been deleted" in resp.data
        assert models.get_student_by_id(sid, db_path=temp_db) is None

    def test_export_students_csv(self, auth_client, temp_db):
        models.create_student("192210508", "Csv Student", "Computer Science", "csv@test.com", 91.0, db_path=temp_db)
        resp = auth_client.get('/students/export')
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'
        assert b"192210508,Csv Student,Computer Science,csv@test.com,91.00,A+,Pass" in resp.data

    def test_testing_dashboard_renders(self, auth_client):
        resp = auth_client.get('/testing/dashboard')
        assert resp.status_code == 200
        assert b"Automated Testing Dashboard" in resp.data

    def test_export_test_report_csv(self, auth_client, temp_db):
        # Empty test runs should redirect with warning
        resp_empty = auth_client.get('/testing/export', follow_redirects=True)
        assert resp_empty.status_code == 200
        assert b"No test report available" in resp_empty.data

        # Record a run and export
        sample_json = json.dumps({
            "test_cases": [
                {"name": "test_sample", "file": "tests/test_bva.py", "type": "Boundary Value Analysis (BVA)", "status": "Passed", "duration": 0.01, "message": "OK"}
            ]
        })
        models.record_test_run("2026-11-25 08:30:00", 1, 1, 0, 0, 0.01, 95.0, sample_json, db_path=temp_db)
        resp_csv = auth_client.get('/testing/export')
        assert resp_csv.status_code == 200
        assert resp_csv.mimetype == 'text/csv'
        assert b"test_sample" in resp_csv.data

    def test_defect_tracking_routes(self, auth_client, temp_db):
        payload = {
            'bug_id': 'BUG-501',
            'module': 'Student Record Management',
            'title': 'Test Integration Defect',
            'severity': 'Medium',
            'status': 'Open',
            'description': 'Integration testing logged defect',
            'steps_to_reproduce': 'Step 1, Step 2',
            'found_by_test': 'test_integration.py',
            'resolution_notes': ''
        }
        resp = auth_client.post('/testing/defects/add', data=payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"BUG-501" in resp.data
        assert b"Test Integration Defect" in resp.data

        resp_list = auth_client.get('/testing/defects?status=Open&severity=Medium')
        assert resp_list.status_code == 200
        assert b"BUG-501" in resp_list.data

    def test_view_nonexistent_student_redirects(self, auth_client):
        resp = auth_client.get('/students/99999', follow_redirects=True)
        assert resp.status_code == 200
        assert b"Student record not found" in resp.data

    def test_edit_nonexistent_student_redirects(self, auth_client):
        resp = auth_client.get('/students/99999/edit', follow_redirects=True)
        assert resp.status_code == 200
        assert b"Student record not found" in resp.data

    def test_delete_nonexistent_student_handled(self, auth_client):
        resp = auth_client.post('/students/99999/delete', follow_redirects=True)
        assert resp.status_code == 200
        assert b"Student record not found" in resp.data

    def test_add_student_invalid_fields(self, auth_client):
        payload = {
            'register_number': '192210550',
            'name': '12345',
            'department': 'Astronomy',
            'email': 'bad_email',
            'marks': '120'
        }
        resp = auth_client.post('/students/add', data=payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Please correct the validation errors highlighted below" in resp.data

    def test_edit_student_invalid_submission(self, auth_client, temp_db):
        sid = models.create_student("192210560", "Valid Student", "Computer Science", "valid@test.com", 80.0, db_path=temp_db)
        payload = {
            'register_number': '192210560',
            'name': 'Valid Student',
            'department': 'Computer Science',
            'email': 'valid@test.com',
            'marks': '-25'
        }
        resp = auth_client.post(f'/students/{sid}/edit', data=payload, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Please correct the validation errors highlighted below" in resp.data

    def test_defect_add_get_and_post_validation_error(self, auth_client):
        resp = auth_client.get('/testing/defects/add')
        assert resp.status_code == 200
        assert b"Log New Defect" in resp.data

        resp_err = auth_client.post('/testing/defects/add', data={'bug_id': 'BUG-999', 'title': '', 'description': '', 'module': ''}, follow_redirects=True)
        assert resp_err.status_code == 200
        assert b"required fields" in resp_err.data

    def test_defect_edit_workflow(self, auth_client, temp_db):
        did = models.create_defect(
            bug_id="BUG-502",
            title="UI Alignment",
            description="Button alignment issue",
            steps_to_reproduce="Open page",
            module="Testing Dashboard",
            severity="Low",
            status="Open",
            db_path=temp_db
        )
        resp = auth_client.get(f'/testing/defects/{did}/edit')
        assert resp.status_code == 200
        assert b"UI Alignment" in resp.data

        edit_payload = {
            'module': 'Testing Dashboard',
            'title': 'UI Alignment Fixed',
            'description': 'Updated alignment css',
            'steps_to_reproduce': 'Open page',
            'severity': 'Low',
            'status': 'Resolved',
            'resolution_notes': 'Applied flexbox alignment'
        }
        resp_up = auth_client.post(f'/testing/defects/{did}/edit', data=edit_payload, follow_redirects=True)
        assert resp_up.status_code == 200
        assert b"updated successfully" in resp_up.data

    def test_defect_edit_nonexistent(self, auth_client):
        resp = auth_client.get('/testing/defects/99999/edit', follow_redirects=True)
        assert resp.status_code == 200
        assert b"Defect record not found" in resp.data

    def test_defect_delete_workflow(self, auth_client, temp_db):
        did = models.create_defect("BUG-503", "Del Defect", "Desc", "Steps", "Module", "Low", "Closed", db_path=temp_db)
        resp = auth_client.post(f'/testing/defects/{did}/delete', follow_redirects=True)
        assert resp.status_code == 200
        assert b"deleted" in resp.data
        assert models.get_defect_by_id(did, db_path=temp_db) is None

    def test_login_page_title_and_student_dashboard(self, auth_client):
        resp = auth_client.get('/students?sort=marks&dir=asc&page=1')
        assert resp.status_code == 200
        assert b"Student Directory" in resp.data

    def test_defect_view_and_audit_trail_routes(self, auth_client, temp_db):
        did = models.create_defect("BUG-601", "Audit Defect Check", "Desc", "Step 1", "Student Record Management", "Medium", "Open", db_path=temp_db)
        resp_view = auth_client.get(f'/testing/defects/{did}')
        assert resp_view.status_code == 200
        assert b"BUG-601" in resp_view.data
        assert b"Audit Defect Check" in resp_view.data

        # Transition lifecycle status: Open -> In Progress -> Resolved
        resp_prog = auth_client.post(f'/testing/defects/{did}/status', data={'status': 'In Progress'}, follow_redirects=True)
        assert resp_prog.status_code == 200
        assert b"In Progress" in resp_prog.data

        resp_res = auth_client.post(f'/testing/defects/{did}/status', data={'status': 'Resolved'}, follow_redirects=True)
        assert resp_res.status_code == 200
        assert b"Re-run the Regression Suite" in resp_res.data

        resp_non = auth_client.get('/testing/defects/99999', follow_redirects=True)
        assert resp_non.status_code == 200
        assert b"Defect record not found" in resp_non.data

        resp_audit = auth_client.get('/testing/audit')
        assert resp_audit.status_code == 200
        assert b"System Audit Trail" in resp_audit.data

    def test_methodology_page_renders(self, auth_client):
        resp = auth_client.get('/testing/methodology')
        assert resp.status_code == 200
        assert b"QA Specifications" in resp.data
        assert b"Boundary Value Analysis" in resp.data
        assert b"Equivalence Class Partitioning" in resp.data

    def test_filter_students_by_department_and_search(self, auth_client, temp_db):
        models.create_student("192210570", "Deepak Chopra", "Mechanical Engineering", "deepak@mech.edu", 78.0, db_path=temp_db)
        models.create_student("192210571", "Sanjay Dutt", "Civil Engineering", "sanjay@civil.edu", 62.0, db_path=temp_db)

        resp = auth_client.get('/students?search=Deepak&department=Mechanical+Engineering')
        assert resp.status_code == 200
        assert b"Deepak Chopra" in resp.data
        assert b"Sanjay Dutt" not in resp.data

    def test_trigger_automated_tests_workflow(self, auth_client, monkeypatch):
        dummy_results = {
            'suite': 'bva',
            'total_tests': 22,
            'passed': 22,
            'failed': 0,
            'skipped': 0,
            'duration': 0.25,
            'pass_rate': 100.0,
            'coverage': {'overall_percent': 94.0, 'files': []},
            'test_cases': [],
            'criteria_met': True,
            'criteria': []
        }
        import test_runner
        monkeypatch.setattr(test_runner, 'run_tests_and_coverage', lambda **kwargs: dummy_results)

        resp = auth_client.post('/testing/run', data={'suite': 'bva'}, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['total_tests'] == 22
        assert data['passed'] == 22

        resp_form = auth_client.post('/testing/run', data={'suite': 'all'}, follow_redirects=True)
        assert resp_form.status_code == 200
        assert b"Automated test run" in resp_form.data
