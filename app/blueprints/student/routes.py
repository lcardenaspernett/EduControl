# app/blueprints/student/routes.py
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import User, Course, Subject, Grade, Attendance, Assignment, Submission
from . import student_bp

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name not in ['student', 'admin']:
            flash('Acceso denegado. Se requieren permisos de estudiante.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Dashboard principal del estudiante con estadísticas mejoradas"""
    try:
        # Obtener cursos con una sola consulta optimizada
        courses = db.session.query(Course).join(Course.students).filter(
            User.id == current_user.id
        ).all()
        
        # Estadísticas básicas optimizadas
        total_courses = len(courses)
        
        # Contar materias con una consulta optimizada
        total_subjects = db.session.query(func.count(Subject.id)).join(Course).join(
            Course.students
        ).filter(User.id == current_user.id).scalar() or 0
        
        # Tareas pendientes con mejor filtrado
        today = date.today()
        pending_assignments = db.session.query(func.count(Assignment.id)).join(
            Subject
        ).join(Course).join(Course.students).filter(
            and_(
                User.id == current_user.id,
                Assignment.due_date >= today,
                ~Assignment.id.in_(
                    db.session.query(Submission.assignment_id).filter(
                        and_(
                            Submission.student_id == current_user.id,
                            Submission.status == 'submitted'
                        )
                    )
                )
            )
        ).scalar() or 0
        
        # Tareas próximas a vencer (siguientes 7 días)
        upcoming_assignments = Assignment.query.join(Subject).join(Course).join(
            Course.students
        ).filter(
            and_(
                User.id == current_user.id,
                Assignment.due_date >= today,
                Assignment.due_date <= today + timedelta(days=7),
                ~Assignment.id.in_(
                    db.session.query(Submission.assignment_id).filter(
                        and_(
                            Submission.student_id == current_user.id,
                            Submission.status == 'submitted'
                        )
                    )
                )
            )
        ).order_by(Assignment.due_date.asc()).limit(5).all()
        
        # Promedio general mejorado con manejo de errores
        grades = db.session.query(Grade.value).filter(
            and_(
                Grade.student_id == current_user.id,
                Grade.value.isnot(None)
            )
        ).all()
        
        average = 0
        if grades:
            valid_grades = [g.value for g in grades if g.value is not None]
            average = sum(valid_grades) / len(valid_grades) if valid_grades else 0
        
        # Estadísticas de asistencia del mes actual
        current_month = date.today().month
        current_year = date.today().year
        
        attendance_stats = db.session.query(
            Attendance.status,
            func.count(Attendance.id)
        ).filter(
            and_(
                Attendance.student_id == current_user.id,
                func.extract('month', Attendance.date) == current_month,
                func.extract('year', Attendance.date) == current_year
            )
        ).group_by(Attendance.status).all()
        
        attendance_summary = {status: count for status, count in attendance_stats}
        
        # Calificaciones recientes
        recent_grades = db.session.query(Grade, Subject).join(Subject).filter(
            Grade.student_id == current_user.id
        ).order_by(Grade.updated_at.desc()).limit(5).all()
        
        return render_template('student/dashboard.html',
                             courses=courses,
                             total_courses=total_courses,
                             total_subjects=total_subjects,
                             pending_assignments=pending_assignments,
                             upcoming_assignments=upcoming_assignments,
                             average=round(average, 2),
                             attendance_summary=attendance_summary,
                             recent_grades=recent_grades)
    
    except Exception as e:
        app.logger.error(f"Error en dashboard del estudiante: {str(e)}")
        flash('Error al cargar el dashboard. Intenta de nuevo.', 'error')
        return render_template('student/dashboard.html',
                             courses=[],
                             total_courses=0,
                             total_subjects=0,
                             pending_assignments=0,
                             upcoming_assignments=[],
                             average=0,
                             attendance_summary={},
                             recent_grades=[])

@student_bp.route('/courses')
@login_required
@student_required
def courses():
    """Lista de cursos del estudiante con estadísticas"""
    try:
        # Consulta optimizada con estadísticas por curso
        courses_data = []
        courses = current_user.enrolled_courses
        
        for course in courses:
            # Contar materias
            subjects_count = len(course.subjects)
            
            # Promedio del curso
            course_grades = db.session.query(Grade.value).join(Subject).filter(
                and_(
                    Subject.course_id == course.id,
                    Grade.student_id == current_user.id,
                    Grade.value.isnot(None)
                )
            ).all()
            
            course_average = 0
            if course_grades:
                valid_grades = [g.value for g in course_grades if g.value is not None]
                course_average = sum(valid_grades) / len(valid_grades) if valid_grades else 0
            
            # Tareas pendientes del curso
            pending = db.session.query(func.count(Assignment.id)).join(Subject).filter(
                and_(
                    Subject.course_id == course.id,
                    Assignment.due_date >= date.today(),
                    ~Assignment.id.in_(
                        db.session.query(Submission.assignment_id).filter(
                            and_(
                                Submission.student_id == current_user.id,
                                Submission.status == 'submitted'
                            )
                        )
                    )
                )
            ).scalar() or 0
            
            courses_data.append({
                'course': course,
                'subjects_count': subjects_count,
                'average': round(course_average, 2),
                'pending_assignments': pending
            })
        
        return render_template('student/courses.html', courses_data=courses_data)
    
    except Exception as e:
        app.logger.error(f"Error al cargar cursos: {str(e)}")
        flash('Error al cargar los cursos. Intenta de nuevo.', 'error')
        return render_template('student/courses.html', courses_data=[])

@student_bp.route('/course/<int:course_id>')
@login_required
@student_required
def course_detail(course_id):
    """Detalle de un curso específico con información completa"""
    try:
        course = Course.query.get_or_404(course_id)
        
        # Verificar que el estudiante está inscrito en este curso
        if course not in current_user.enrolled_courses:
            flash('No tienes acceso a este curso.', 'error')
            return redirect(url_for('student.courses'))
        
        # Obtener materias con estadísticas
        subjects_data = []
        for subject in course.subjects:
            # Calificación de la materia
            grade = Grade.query.filter_by(
                student_id=current_user.id,
                subject_id=subject.id
            ).first()
            
            # Tareas de la materia
            assignments = Assignment.query.filter_by(subject_id=subject.id).all()
            completed_assignments = 0
            
            for assignment in assignments:
                submission = Submission.query.filter_by(
                    assignment_id=assignment.id,
                    student_id=current_user.id,
                    status='submitted'
                ).first()
                if submission:
                    completed_assignments += 1
            
            subjects_data.append({
                'subject': subject,
                'grade': grade.value if grade else None,
                'total_assignments': len(assignments),
                'completed_assignments': completed_assignments
            })
        
        return render_template('student/course_detail.html',
                             course=course,
                             subjects_data=subjects_data)
    
    except Exception as e:
        app.logger.error(f"Error al cargar detalle del curso {course_id}: {str(e)}")
        flash('Error al cargar el curso. Intenta de nuevo.', 'error')
        return redirect(url_for('student.courses'))

@student_bp.route('/grades')
@login_required
@student_required
def grades():
    """Ver calificaciones del estudiante con estadísticas mejoradas"""
    try:
        courses = current_user.enrolled_courses
        grades_data = {}
        overall_stats = {'total_grades': 0, 'average': 0, 'highest': 0, 'lowest': 100}
        all_grades = []
        
        for course in courses:
            grades_data[course.id] = {
                'course': course,
                'subjects': [],
                'course_average': 0
            }
            
            course_grades = []
            for subject in course.subjects:
                grade = Grade.query.filter_by(
                    student_id=current_user.id,
                    subject_id=subject.id
                ).first()
                
                grade_value = grade.value if grade and grade.value else None
                if grade_value is not None:
                    course_grades.append(grade_value)
                    all_grades.append(grade_value)
                
                grades_data[course.id]['subjects'].append({
                    'subject': subject,
                    'grade': grade_value,
                    'updated_at': grade.updated_at if grade else None
                })
            
            # Promedio del curso
            if course_grades:
                grades_data[course.id]['course_average'] = round(
                    sum(course_grades) / len(course_grades), 2
                )
        
        # Estadísticas generales
        if all_grades:
            overall_stats['total_grades'] = len(all_grades)
            overall_stats['average'] = round(sum(all_grades) / len(all_grades), 2)
            overall_stats['highest'] = max(all_grades)
            overall_stats['lowest'] = min(all_grades)
        
        return render_template('student/grades.html', 
                             grades_data=grades_data,
                             overall_stats=overall_stats)
    
    except Exception as e:
        app.logger.error(f"Error al cargar calificaciones: {str(e)}")
        flash('Error al cargar las calificaciones. Intenta de nuevo.', 'error')
        return render_template('student/grades.html', grades_data={}, overall_stats={})

@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    """Ver registro de asistencia con estadísticas mejoradas"""
    try:
        # Obtener mes y año seleccionados con validación
        month = int(request.args.get('month', date.today().month))
        year = int(request.args.get('year', date.today().year))
        
        # Validar mes y año
        if month < 1 or month > 12:
            month = date.today().month
        if year < 2020 or year > date.today().year + 1:
            year = date.today().year
        
        # Obtener registros de asistencia del mes con consulta optimizada
        attendance_records = db.session.query(Attendance).filter(
            and_(
                Attendance.student_id == current_user.id,
                func.extract('month', Attendance.date) == month,
                func.extract('year', Attendance.date) == year
            )
        ).all()
        
        # Organizar por fecha y calcular estadísticas
        attendance_data = {}
        stats = {'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
        
        for record in attendance_records:
            attendance_data[record.date.day] = {
                'status': record.status,
                'notes': record.notes or ''
            }
            stats[record.status] = stats.get(record.status, 0) + 1
        
        # Calcular porcentaje de asistencia
        total_days = sum(stats.values())
        attendance_percentage = 0
        if total_days > 0:
            attendance_percentage = round((stats['present'] / total_days) * 100, 2)
        
        return render_template('student/attendance.html',
                             attendance_data=attendance_data,
                             current_month=month,
                             current_year=year,
                             stats=stats,
                             attendance_percentage=attendance_percentage)
    
    except Exception as e:
        app.logger.error(f"Error al cargar asistencia: {str(e)}")
        flash('Error al cargar la asistencia. Intenta de nuevo.', 'error')
        return render_template('student/attendance.html',
                             attendance_data={},
                             current_month=date.today().month,
                             current_year=date.today().year,
                             stats={},
                             attendance_percentage=0)

@student_bp.route('/assignments')
@login_required
@student_required
def assignments():
    """Ver tareas asignadas con filtros y estadísticas"""
    try:
        # Filtros
        status_filter = request.args.get('status', 'all')  # all, pending, completed, overdue
        subject_filter = request.args.get('subject', 'all')
        
        # Query base optimizada
        query = db.session.query(Assignment).join(Subject).join(Course).join(
            Course.students
        ).filter(User.id == current_user.id)
        
        # Aplicar filtro de materia
        if subject_filter != 'all':
            query = query.filter(Subject.id == subject_filter)
        
        assignments = query.order_by(Assignment.due_date.desc()).all()
        
        # Obtener submissions del estudiante
        submissions = {}
        assignment_ids = [a.id for a in assignments]
        if assignment_ids:
            student_submissions = db.session.query(Submission).filter(
                and_(
                    Submission.assignment_id.in_(assignment_ids),
                    Submission.student_id == current_user.id
                )
            ).all()
            
            for submission in student_submissions:
                submissions[submission.assignment_id] = submission
        
        # Filtrar por estado
        filtered_assignments = []
        today = date.today()
        
        for assignment in assignments:
            submission = submissions.get(assignment.id)
            is_completed = submission and submission.status == 'submitted'
            is_overdue = assignment.due_date < today and not is_completed
            
            if status_filter == 'all':
                filtered_assignments.append(assignment)
            elif status_filter == 'pending' and not is_completed and not is_overdue:
                filtered_assignments.append(assignment)
            elif status_filter == 'completed' and is_completed:
                filtered_assignments.append(assignment)
            elif status_filter == 'overdue' and is_overdue:
                filtered_assignments.append(assignment)
        
        # Estadísticas
        total_assignments = len(assignments)
        completed_count = len([a for a in assignments if submissions.get(a.id) and submissions[a.id].status == 'submitted'])
        pending_count = len([a for a in assignments if not (submissions.get(a.id) and submissions[a.id].status == 'submitted') and a.due_date >= today])
        overdue_count = len([a for a in assignments if not (submissions.get(a.id) and submissions[a.id].status == 'submitted') and a.due_date < today])
        
        # Obtener materias para el filtro
        subjects = db.session.query(Subject).join(Course).join(Course.students).filter(
            User.id == current_user.id
        ).all()
        
        return render_template('student/assignments.html',
                             assignments=filtered_assignments,
                             submissions=submissions,
                             subjects=subjects,
                             current_status=status_filter,
                             current_subject=subject_filter,
                             stats={
                                 'total': total_assignments,
                                 'completed': completed_count,
                                 'pending': pending_count,
                                 'overdue': overdue_count
                             })
        
    except Exception as e:
        app.logger.error(f"Error al cargar tareas: {str(e)}")
        flash('Error al cargar las tareas. Intenta de nuevo.', 'error')
        return render_template('student/assignments.html',
                             assignments=[],
                             submissions={},
                             subjects=[],
                             current_status='all',
                             current_subject='all',
                             stats={})

@student_bp.route('/assignment/<int:assignment_id>')
@login_required
@student_required
def assignment_detail(assignment_id):
    """Detalle de una tarea específica"""
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        
        # Verificar acceso
        if assignment.subject.course not in current_user.enrolled_courses:
            flash('No tienes acceso a esta tarea.', 'error')
            return redirect(url_for('student.assignments'))
        
        # Obtener submission si existe
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
        
        # Información adicional
        is_overdue = assignment.due_date < date.today()
        can_submit = not is_overdue or (submission and submission.status != 'submitted')
        
        return render_template('student/assignment_detail.html',
                             assignment=assignment,
                             submission=submission,
                             is_overdue=is_overdue,
                             can_submit=can_submit)
        
    except Exception as e:
        app.logger.error(f"Error al cargar tarea {assignment_id}: {str(e)}")
        flash('Error al cargar la tarea. Intenta de nuevo.', 'error')
        return redirect(url_for('student.assignments'))

@student_bp.route('/schedule')
@login_required
@student_required
def schedule():
    """Ver horario de clases con información detallada"""
    try:
        courses = current_user.enrolled_courses
        
        # Organizar por días de la semana (si tienes esa información en tu modelo)
        schedule_data = {}
        for course in courses:
            # Aquí puedes agregar lógica para organizar por horarios
            # si tienes un modelo de Schedule o información de horarios
            schedule_data[course.id] = {
                'course': course,
                'subjects': course.subjects,
                # 'schedule_times': course.schedule_times  # Si existe
            }
        
        return render_template('student/schedule.html', 
                             courses=courses,
                             schedule_data=schedule_data)
        
    except Exception as e:
        app.logger.error(f"Error al cargar horario: {str(e)}")
        flash('Error al cargar el horario. Intenta de nuevo.', 'error')
        return render_template('student/schedule.html', courses=[], schedule_data={})

# API Routes Mejoradas

@student_bp.route('/api/submit-assignment', methods=['POST'])
@login_required
@student_required
def submit_assignment():
    """Enviar tarea con validaciones mejoradas"""
    try:
        assignment_id = request.form.get('assignment_id')
        content = request.form.get('content', '').strip()
        
        # Validaciones básicas
        if not assignment_id:
            return jsonify({'success': False, 'message': 'ID de tarea requerido'}), 400
        
        if not content:
            return jsonify({'success': False, 'message': 'El contenido es requerido'}), 400
        
        assignment = Assignment.query.get_or_404(assignment_id)
        
        # Verificar acceso
        if assignment.subject.course not in current_user.enrolled_courses:
            return jsonify({'success': False, 'message': 'Sin acceso a esta tarea'}), 403
        
        # Verificar fecha límite (permitir envío con advertencia si está vencida)
        is_overdue = assignment.due_date < date.today()
        
        # Buscar o crear submission
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
        
        if submission:
            submission.content = content
            submission.submitted_at = datetime.utcnow()
            submission.status = 'submitted'
            if is_overdue:
                submission.notes = 'Entregada fuera de plazo'
        else:
            submission = Submission(
                assignment_id=assignment_id,
                student_id=current_user.id,
                content=content,
                status='submitted',
                notes='Entregada fuera de plazo' if is_overdue else None
            )
            db.session.add(submission)
        
        db.session.commit()
        
        message = 'Tarea enviada correctamente'
        if is_overdue:
            message += ' (fuera de plazo)'
        
        return jsonify({
            'success': True, 
            'message': message,
            'is_overdue': is_overdue
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al enviar tarea: {str(e)}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@student_bp.route('/api/upload-file', methods=['POST'])
@login_required
@student_required
def upload_file():
    """Subir archivo para una tarea"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No se seleccionó archivo'}), 400
        
        file = request.files['file']
        assignment_id = request.form.get('assignment_id')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No se seleccionó archivo'}), 400
        
        if not assignment_id:
            return jsonify({'success': False, 'message': 'ID de tarea requerido'}), 400
        
        assignment = Assignment.query.get_or_404(assignment_id)
        
        # Verificar acceso
        if assignment.subject.course not in current_user.enrolled_courses:
            return jsonify({'success': False, 'message': 'Sin acceso'}), 403
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Agregar timestamp para evitar conflictos
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{assignment_id}_{timestamp}_{filename}"
            
            # Crear directorio si no existe
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'assignments')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            # Actualizar o crear submission
            submission = Submission.query.filter_by(
                assignment_id=assignment_id,
                student_id=current_user.id
            ).first()
            
            if submission:
                submission.file_path = filepath
                submission.file_name = file.filename
            else:
                submission = Submission(
                    assignment_id=assignment_id,
                    student_id=current_user.id,
                    file_path=filepath,
                    file_name=file.filename,
                    status='draft'
                )
                db.session.add(submission)
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Archivo subido correctamente',
                'filename': file.filename
            })
        else:
            return jsonify({'success': False, 'message': 'Tipo de archivo no permitido'}), 400
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al subir archivo: {str(e)}")
        return jsonify({'success': False, 'message': 'Error al subir archivo'}), 500

@student_bp.route('/api/statistics')
@login_required
@student_required
def get_statistics():
    """Obtener estadísticas detalladas del estudiante"""
    try:
        # Estadísticas generales
        total_courses = len(current_user.enrolled_courses)
        
        # Calificaciones
        grades = db.session.query(Grade.value).filter(
            and_(
                Grade.student_id == current_user.id,
                Grade.value.isnot(None)
            )
        ).all()
        
        grade_stats = {
            'count': len(grades),
            'average': 0,
            'highest': 0,
            'lowest': 0
        }
        
        if grades:
            values = [g.value for g in grades]
            grade_stats['average'] = round(sum(values) / len(values), 2)
            grade_stats['highest'] = max(values)
            grade_stats['lowest'] = min(values)
        
        # Tareas
        today = date.today()
        all_assignments = db.session.query(Assignment.id).join(Subject).join(Course).join(
            Course.students
        ).filter(User.id == current_user.id).all()
        
        submitted_assignments = db.session.query(Submission.assignment_id).filter(
            and_(
                Submission.student_id == current_user.id,
                Submission.status == 'submitted'
            )
        ).all()
        
        assignment_stats = {
            'total': len(all_assignments),
            'completed': len(submitted_assignments),
            'pending': len(all_assignments) - len(submitted_assignments)
        }
        
        # Asistencia del mes actual
        current_month = date.today().month
        current_year = date.today().year
        
        attendance_records = db.session.query(Attendance.status).filter(
            and_(
                Attendance.student_id == current_user.id,
                func.extract('month', Attendance.date) == current_month,
                func.extract('year', Attendance.date) == current_year
            )
        ).all()
        
        attendance_stats = {}
        for record in attendance_records:
            status = record.status
            attendance_stats[status] = attendance_stats.get(status, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'courses': total_courses,
                'grades': grade_stats,
                'assignments': assignment_stats,
                'attendance': attendance_stats
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error al obtener estadísticas: {str(e)}")
        return jsonify({'success': False, 'message': 'Error al obtener estadísticas'}), 500