"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

Base = declarative_base()

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    max_participants = Column(Integer, nullable=False)
    enrollments = relationship("Enrollment", back_populates="activity")

class Enrollment(Base):
    __tablename__ = 'enrollments'
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False)
    email = Column(String, nullable=False)
    activity = relationship("Activity", back_populates="enrollments")

# Create engine
engine = create_engine('sqlite:///activities.db', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to initialize database with data
def init_db():
    db = SessionLocal()
    if db.query(Activity).count() == 0:
        activities_data = [
            {"name": "Chess Club", "description": "Learn strategies and compete in chess tournaments", "schedule": "Fridays, 3:30 PM - 5:00 PM", "max_participants": 12, "participants": ["michael@mergington.edu", "daniel@mergington.edu"]},
            {"name": "Programming Class", "description": "Learn programming fundamentals and build software projects", "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", "max_participants": 20, "participants": ["emma@mergington.edu", "sophia@mergington.edu"]},
            {"name": "Gym Class", "description": "Physical education and sports activities", "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", "max_participants": 30, "participants": ["john@mergington.edu", "olivia@mergington.edu"]},
            {"name": "Soccer Team", "description": "Join the school soccer team and compete in matches", "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", "max_participants": 22, "participants": ["liam@mergington.edu", "noah@mergington.edu"]},
            {"name": "Basketball Team", "description": "Practice and play basketball with the school team", "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM", "max_participants": 15, "participants": ["ava@mergington.edu", "mia@mergington.edu"]},
            {"name": "Art Club", "description": "Explore your creativity through painting and drawing", "schedule": "Thursdays, 3:30 PM - 5:00 PM", "max_participants": 15, "participants": ["amelia@mergington.edu", "harper@mergington.edu"]},
            {"name": "Drama Club", "description": "Act, direct, and produce plays and performances", "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM", "max_participants": 20, "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]},
            {"name": "Math Club", "description": "Solve challenging problems and participate in math competitions", "schedule": "Tuesdays, 3:30 PM - 4:30 PM", "max_participants": 10, "participants": ["james@mergington.edu", "benjamin@mergington.edu"]},
            {"name": "Debate Team", "description": "Develop public speaking and argumentation skills", "schedule": "Fridays, 4:00 PM - 5:30 PM", "max_participants": 12, "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]}
        ]
        for data in activities_data:
            participants = data.pop("participants")
            activity = Activity(**data)
            db.add(activity)
            db.flush()
            for email in participants:
                enrollment = Enrollment(activity_id=activity.id, email=email)
                db.add(enrollment)
        db.commit()
    db.close()

init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    db = SessionLocal()
    activities = db.query(Activity).all()
    result = {}
    for act in activities:
        participants = [e.email for e in act.enrollments]
        result[act.name] = {
            "description": act.description,
            "schedule": act.schedule,
            "max_participants": act.max_participants,
            "participants": participants
        }
    db.close()
    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    db = SessionLocal()
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        db.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    if email in [e.email for e in activity.enrollments]:
        db.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")
    if len(activity.enrollments) >= activity.max_participants:
        db.close()
        raise HTTPException(status_code=400, detail="Activity is full")
    enrollment = Enrollment(activity_id=activity.id, email=email)
    db.add(enrollment)
    db.commit()
    db.close()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    db = SessionLocal()
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        db.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    enrollment = db.query(Enrollment).filter(Enrollment.activity_id == activity.id, Enrollment.email == email).first()
    if not enrollment:
        db.close()
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")
    db.delete(enrollment)
    db.commit()
    db.close()
    return {"message": f"Unregistered {email} from {activity_name}"}
