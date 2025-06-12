# app/blueprints/teacher/routes.py
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
from sqlalchemy import and_
from app import db
from app.models import User, Course, Subject, Grade, Attendance, Assignment, Submission
from . import teacher_bp

def teacher_required(f):
    """Decorador para verificar permisos de profesor"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name not in ['teacher', 'admin']:
            flash('Acceso denegado. Se requieren permisos de profesor.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Dashboard principal del profesor"""
    try:
        # Obtener cursos asignados al profesor
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        
        # Estadísticas básicas
        total_students = sum(len(course.students) for course in courses)
        total_subjects = Subject.query.join(Course).filter(Course.teacher_id == current_user.id).count()
        
        # Tareas pendientes de calificar
        pending_submissions = Submission.query.join(Assignment).join(Subject).join(Course).filter(
            Course.teacher_id == current_user.id,
            Submission.grade.is_(None)
        ).count()
        
        # Asistencias pendientes de hoy
        today = date.today()
        pending_attendance = 0
        for course in courses:
            for student in course.students:
                attendance_exists = Attendance.query.filter_by(
                    student_id=student.id,
                    date=today
                ).first()
                if not attendance_exists:
                    pending_attendance += 1
        
        return render_template('teacher/dashboard.html',
                             courses=courses,
                             total_students=total_students,
                             total_subjects=total_subjects,
                             pending_submissions=pending_submissions,
                             pending_attendance=pending_attendance)
    except Exception as e:
        flash(f'Error al cargar el dashboard: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@teacher_bp.route('/courses')
@login_required
@teacher_required
def courses():
    """Lista de cursos del profesor"""
    try:
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher/courses.html', courses=courses)
    except Exception as e:
        flash(f'Error al cargar los cursos: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/course/<int:course_id>')
@login_required
@teacher_required
def course_detail(course_id):
    """Detalle de un curso específico"""
    try:
        course = Course.query.get_or_404(course_id)
        
        # Verificar que el profesor tiene acceso a este curso
        if course.teacher_id != current_user.id:
            flash('No tienes permisos para acceder a este curso.', 'error')
            return redirect(url_for('teacher.courses'))
        
        # Obtener estadísticas del curso
        total_students = len(course.students)
        subjects = Subject.query.filter_by(course_id=course_id).all()
        
        # Estadísticas adicionales
        total_assignments = Assignment.query.join(Subject).filter(Subject.course_id == course_id).count()
        avg_attendance = 0
        if course.students:
            total_days = Attendance.query.filter(
                Attendance.student_id.in_([s.id for s in course.students])
            ).with_entities(Attendance.date).distinct().count()
            
            if total_days > 0:
                present_count = Attendance.query.filter(
                    Attendance.student_id.in_([s.id for s in course.students]),
                    Attendance.status == 'present'
                ).count()
                avg_attendance = round((present_count / (total_days * len(course.students))) * 100, 1)
        
        return render_template('teacher/course_detail.html',
                             course=course,
                             total_students=total_students,
                             subjects=subjects,
                             total_assignments=total_assignments,
                             avg_attendance=avg_attendance)
    except Exception as e:
        flash(f'Error al cargar el detalle del curso: {str(e)}', 'error')
        return redirect(url_for('teacher.courses'))

@teacher_bp.route('/grades')
@login_required
@teacher_required
def grades():
    """Gestión de calificaciones"""
    try:
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher/grades.html', courses=courses)
    except Exception as e:
        flash(f'Error al cargar las calificaciones: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/course/<int:course_id>/grades')
@login_required
@teacher_required
def course_grades(course_id):
    """Calificaciones de un curso específico"""
    try:
        course = Course.query.get_or_404(course_id)
        
        if course.teacher_id != current_user.id:
            flash('No tienes permisos para acceder a este curso.', 'error')
            return redirect(url_for('teacher.grades'))
        
        subjects = Subject.query.filter_by(course_id=course_id).all()
        students = course.students
        
        # Obtener calificaciones de manera más eficiente
        grades_query = Grade.query.filter(
            Grade.student_id.in_([s.id for s in students]),
            Grade.subject_id.in_([sub.id for sub in subjects])
        ).all()
        
        # Organizar calificaciones por estudiante y materia
        grades_data = {}
        for student in students:
            grades_data[student.id] = {}
            for subject in subjects:
                grades_data[student.id][subject.id] = None
        
        for grade in grades_query:
            grades_data[grade.student_id][grade.subject_id] = grade.value
        
        return render_template('teacher/course_grades.html',
                             course=course,
                             subjects=subjects,
                             students=students,
                             grades_data=grades_data)
    except Exception as e:
        flash(f'Error al cargar las calificaciones del curso: {str(e)}', 'error')
        return redirect(url_for('teacher.grades'))

@teacher_bp.route('/attendance')
@login_required
@teacher_required
def attendance():
    """Gestión de asistencia"""
    try:
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher/attendance.html', courses=courses)
    except Exception as e:
        flash(f'Error al cargar la asistencia: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/course/<int:course_id>/attendance')
@login_required
@teacher_required
def course_attendance(course_id):
    """Asistencia de un curso específico"""
    try:
        course = Course.query.get_or_404(course_id)
        
        if course.teacher_id != current_user.id:
            flash('No tienes permisos para acceder a este curso.', 'error')
            return redirect(url_for('teacher.attendance'))
        
        # Obtener fecha seleccionada o usar hoy
        selected_date_str = request.args.get('date', date.today().isoformat())
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
        
        students = course.students
        
        # Obtener asistencias de manera más eficiente
        attendance_query = Attendance.query.filter(
            Attendance.student_id.in_([s.id for s in students]),
            Attendance.date == selected_date
        ).all()
        
        attendance_data = {}
        for student in students:
            attendance_data[student.id] = None
        
        for attendance in attendance_query:
            attendance_data[attendance.student_id] = attendance.status
        
        return render_template('teacher/course_attendance.html',
                             course=course,
                             students=students,
                             selected_date=selected_date,
                             attendance_data=attendance_data)
    except Exception as e:
        flash(f'Error al cargar la asistencia del curso: {str(e)}', 'error')
        return redirect(url_for('teacher.attendance'))

@teacher_bp.route('/assignments')
@login_required
@teacher_required
def assignments():
    """Gestión de tareas"""
    try:
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        assignments = Assignment.query.join(Subject).join(Course).filter(
            Course.teacher_id == current_user.id
        ).order_by(Assignment.created_at.desc()).all()
        
        return render_template('teacher/assignments.html',
                             courses=courses,
                             assignments=assignments)
    except Exception as e:
        flash(f'Error al cargar las tareas: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/assignment/<int:assignment_id>')
@login_required
@teacher_required
def assignment_detail(assignment_id):
    """Detalle de una tarea específica"""
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        
        # Verificar permisos
        if assignment.subject.course.teacher_id != current_user.id:
            flash('No tienes permisos para acceder a esta tarea.', 'error')
            return redirect(url_for('teacher.assignments'))
        
        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
        
        return render_template('teacher/assignment_detail.html',
                             assignment=assignment,
                             submissions=submissions)
    except Exception as e:
        flash(f'Error al cargar el detalle de la tarea: {str(e)}', 'error')
        return redirect(url_for('teacher.assignments'))

# API Routes para funcionalidad AJAX

@teacher_bp.route('/api/save-grade', methods=['POST'])
@login_required
@teacher_required
def save_grade():
    """Guardar calificación via AJAX"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos no válidos'}), 400
        
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        grade_value = data.get('grade')
        
        if not all([student_id, subject_id]):
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400
        
        # Verificar que el profesor tiene acceso
        subject = Subject.query.get_or_404(subject_id)
        if subject.course.teacher_id != current_user.id:
            return jsonify({'success': False, 'message': 'Sin permisos'}), 403
        
        # Validar el valor de la calificación
        if grade_value is not None:
            try:
                grade_value = float(grade_value)
                if grade_value < 0 or grade_value > 10:  # Asumiendo escala 0-10
                    return jsonify({'success': False, 'message': 'Calificación debe estar entre 0 y 10'}), 400
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Calificación no válida'}), 400
        
        # Buscar o crear calificación
        grade = Grade.query.filter_by(
            student_id=student_id,
            subject_id=subject_id
        ).first()
        
        if grade:
            grade.value = grade_value
            grade.updated_at = datetime.utcnow()
            grade.teacher_id = current_user.id  # Actualizar quien modificó
        else:
            grade = Grade(
                student_id=student_id,
                subject_id=subject_id,
                value=grade_value,
                teacher_id=current_user.id
            )
            db.session.add(grade)
        
        db.session.commit()
        message = 'Calificación eliminada' if grade_value is None else 'Calificación guardada'
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@teacher_bp.route('/api/save-attendance', methods=['POST'])
@login_required
@teacher_required
def save_attendance():
    """Guardar asistencia via AJAX"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos no válidos'}), 400
        
        student_id = data.get('student_id')
        attendance_date_str = data.get('date')
        status = data.get('status')
        
        if not all([student_id, attendance_date_str, status]):
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400
        
        # Validar fecha
        try:
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de fecha no válido'}), 400
        
        # Validar estado
        valid_statuses = ['present', 'absent', 'late', 'excused']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Estado de asistencia no válido'}), 400
        
        # Verificar que el estudiante pertenece a un curso del profesor
        student = User.query.get_or_404(student_id)
        course = None
        for c in student.enrolled_courses:
            if c.teacher_id == current_user.id:
                course = c
                break
        
        if not course:
            return jsonify({'success': False, 'message': 'Sin permisos'}), 403
        
        # Buscar o crear registro de asistencia
        attendance = Attendance.query.filter_by(
            student_id=student_id,
            date=attendance_date
        ).first()
        
        if attendance:
            attendance.status = status
            attendance.updated_at = datetime.utcnow()
            attendance.teacher_id = current_user.id  # Actualizar quien modificó
        else:
            attendance = Attendance(
                student_id=student_id,
                date=attendance_date,
                status=status,
                teacher_id=current_user.id
            )
            db.session.add(attendance)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Asistencia guardada'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@teacher_bp.route('/api/bulk-attendance', methods=['POST'])
@login_required
@teacher_required
def bulk_attendance():
    """Guardar múltiples asistencias a la vez"""
    try:
        data = request.get_json()
        if not data or 'attendances' not in data:
            return jsonify({'success': False, 'message': 'Datos no válidos'}), 400
        
        attendances_data = data['attendances']
        attendance_date_str = data.get('date')
        
        if not attendance_date_str:
            return jsonify({'success': False, 'message': 'Fecha requerida'}), 400
        
        try:
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de fecha no válido'}), 400
        
        updated_count = 0
        valid_statuses = ['present', 'absent', 'late', 'excused']
        
        for attendance_data in attendances_data:
            student_id = attendance_data.get('student_id')
            status = attendance_data.get('status')
            
            if not student_id or status not in valid_statuses:
                continue
            
            # Verificar permisos para cada estudiante
            student = User.query.get(student_id)
            if not student:
                continue
            
            has_permission = False
            for course in student.enrolled_courses:
                if course.teacher_id == current_user.id:
                    has_permission = True
                    break
            
            if not has_permission:
                continue
            
            # Buscar o crear registro
            attendance = Attendance.query.filter_by(
                student_id=student_id,
                date=attendance_date
            ).first()
            
            if attendance:
                attendance.status = status
                attendance.updated_at = datetime.utcnow()
                attendance.teacher_id = current_user.id
            else:
                attendance = Attendance(
                    student_id=student_id,
                    date=attendance_date,
                    status=status,
                    teacher_id=current_user.id
                )
                db.session.add(attendance)
            
            updated_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Se actualizaron {updated_count} registros de asistencia'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@teacher_bp.route('/api/student-stats/<int:student_id>')
@login_required
@teacher_required
def student_stats(student_id):
    """Obtener estadísticas de un estudiante específico"""
    try:
        student = User.query.get_or_404(student_id)
        
        # Verificar permisos
        has_permission = False
        for course in student.enrolled_courses:
            if course.teacher_id == current_user.id:
                has_permission = True
                break
        
        if not has_permission:
            return jsonify({'success': False, 'message': 'Sin permisos'}), 403
        
        # Calcular estadísticas
        total_grades = Grade.query.filter_by(student_id=student_id).count()
        avg_grade = db.session.query(db.func.avg(Grade.value)).filter_by(student_id=student_id).scalar()
        avg_grade = round(avg_grade, 2) if avg_grade else 0
        
        total_attendance = Attendance.query.filter_by(student_id=student_id).count()
        present_days = Attendance.query.filter_by(student_id=student_id, status='present').count()
        attendance_rate = round((present_days / total_attendance) * 100, 1) if total_attendance > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_grades': total_grades,
                'avg_grade': avg_grade,
                'attendance_rate': attendance_rate,
                'total_attendance_records': total_attendance
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500