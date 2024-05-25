import gradio as gr
from pydantic import BaseModel, ValidationError, validator
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# Database setup
DATABASE_URL = "sqlite:///attendance_management.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic models
class Teacher(BaseModel):
    id: int
    name: str
    available_sessions: int = 9

class Subject(BaseModel):
    id: int
    name: str
    teacher_id: int

class Student(BaseModel):
    id: int
    name: str
    grade: str
    section: str

class Attendance(BaseModel):
    id: int
    student_id: int
    subject_id: int
    date: datetime.date
    status: bool

# SQLAlchemy models
class TeacherDB(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    available_sessions = Column(Integer, default=9)

class SubjectDB(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

class StudentDB(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    grade = Column(String, index=True)
    section = Column(String, index=True)

class AttendanceDB(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Gradio interfaces
def admin_portal():
    def create_teacher(name):
        db = SessionLocal()
        teacher = TeacherDB(name=name)
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        db.close()
        return f"Teacher {name} created with ID {teacher.id}"

    def create_subject(name, teacher_id):
        db = SessionLocal()
        subject = SubjectDB(name=name, teacher_id=teacher_id)
        db.add(subject)
        db.commit()
        db.refresh(subject)
        db.close()
        return f"Subject {name} created with ID {subject.id} and assigned to teacher ID {teacher_id}"

    def create_student(name, grade, section):
        db = SessionLocal()
        student = StudentDB(name=name, grade=grade, section=section)
        db.add(student)
        db.commit()
        db.refresh(student)
        db.close()
        return f"Student {name} created with ID {student.id}"

    teacher_interface = gr.Interface(fn=create_teacher, inputs="text", outputs="text", title="Create Teacher")
    subject_interface = gr.Interface(fn=create_subject, inputs=["text", "number"], outputs="text", title="Create Subject")
    student_interface = gr.Interface(fn=create_student, inputs=["text", "text", "text"], outputs="text", title="Create Student")

    return gr.TabbedInterface([teacher_interface, subject_interface, student_interface], ["Create Teacher", "Create Subject", "Create Student"])

def teacher_portal():
    def take_attendance(student_id, subject_id, status):
        db = SessionLocal()
        attendance = AttendanceDB(student_id=student_id, subject_id=subject_id, status=status)
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        db.close()
        return f"Attendance recorded for student ID {student_id} in subject ID {subject_id} with status {status}"

    def generate_report(subject_id):
        db = SessionLocal()
        records = db.query(AttendanceDB).filter(AttendanceDB.subject_id == subject_id).all()
        report = "\n".join([f"Student ID: {record.student_id}, Date: {record.date}, Status: {record.status}" for record in records])
        db.close()
        return report

    attendance_interface = gr.Interface(fn=take_attendance, inputs=["number", "number", "checkbox"], outputs="text", title="Take Attendance")
    report_interface = gr.Interface(fn=generate_report, inputs="number", outputs="text", title="Generate Report")

    return gr.TabbedInterface([attendance_interface, report_interface], ["Take Attendance", "Generate Report"])

def student_portal():
    def check_schedule(student_id):
        db = SessionLocal()
        student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not student:
            return "Student not found"
        subjects = db.query(SubjectDB).join(TeacherDB).filter(SubjectDB.teacher_id == TeacherDB.id).all()
        schedule = "\n".join([f"Subject: {subject.name}, Teacher: {subject.teacher_id}" for subject in subjects])
        db.close()
        return schedule

    def log_attendance(student_id, subject_id):
        db = SessionLocal()
        attendance = AttendanceDB(student_id=student_id, subject_id=subject_id, status=True)
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        db.close()
        return f"Attendance logged for student ID {student_id} in subject ID {subject_id}"

    schedule_interface = gr.Interface(fn=check_schedule, inputs="number", outputs="text", title="Check Schedule")
    log_attendance_interface = gr.Interface(fn=log_attendance, inputs=["number", "number"], outputs="text", title="Log Attendance")

    return gr.TabbedInterface([schedule_interface, log_attendance_interface], ["Check Schedule", "Log Attendance"])

# Launch the Gradio app
admin_interface = admin_portal()
teacher_interface = teacher_portal()
student_interface = student_portal()

gr.TabbedInterface([admin_interface, teacher_interface, student_interface], ["Admin Portal", "Teacher Portal", "Student Portal"]).launch()