# models/attendance.py
from datetime import datetime, date
from .database import db

class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default='present')  # present, absent, late, excused
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Relaciones explícitas
    student = db.relationship('User', foreign_keys=[student_id], backref='attendance_student', lazy=True, overlaps="attendance_student,student_attendances")
    course = db.relationship('Course', foreign_keys=[course_id], backref='attendances')
    
    # Constraint único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'date', name='unique_attendance_per_day'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.student.username} - {self.course.code} - {self.date} - {self.status}>'
    
    @classmethod
    def get_attendance_by_course_and_date(cls, course_id, date):
        return cls.query.filter_by(course_id=course_id, date=date).all()
    
    @classmethod
    def get_student_attendance_summary(cls, student_id, course_id=None):
        query = cls.query.filter_by(student_id=student_id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        
        attendances = query.all()
        total = len(attendances)
        present = len([a for a in attendances if a.status == 'present'])
        
        return {
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': (present / total * 100) if total > 0 else 0
        }