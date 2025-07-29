from sqlalchemy.orm import Session
from .models import User, CompanyDocument
from .connection import SessionLocal, init_db
from ..utils.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

def create_initial_data():
    """Create initial data for the database"""
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.email == "admin@company.com").first()
        if not admin:
            # Create admin user
            admin = User(
                email="admin@company.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                department="IT"
            )
            db.add(admin)
            logger.info("Admin user created")
        
        # Add sample company documents
        if db.query(CompanyDocument).count() == 0:
            documents = [
                CompanyDocument(
                    title="Employee Handbook",
                    content="""Welcome to our company! This handbook outlines our policies and procedures.
                    
                    Work Hours: Our standard work hours are 9 AM to 5 PM, Monday through Friday.
                    
                    Clock-In/Out Policy: Employees must clock in within 15 minutes of their scheduled start time.
                    
                    Task Assignment: Tasks are assigned based on workload and expertise. High-priority tasks should be completed first.
                    
                    Weekly Reports: All employees must submit weekly reports by Friday 5 PM.""",
                    document_type="policy",
                    category="hr"
                ),
                CompanyDocument(
                    title="IT Security Policy",
                    content="""IT Security Guidelines:
                    
                    1. Password must be at least 8 characters
                    2. Do not share login credentials
                    3. Report suspicious activities immediately
                    4. Keep software updated""",
                    document_type="policy",
                    category="it"
                )
            ]
            db.add_all(documents)
            logger.info("Sample documents created")
        
        db.commit()
        logger.info("Initial data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def initialize_database():
    """Initialize database with tables and initial data"""
    logger.info("Initializing database...")
    init_db()
    create_initial_data()
    logger.info("Database initialization complete")

if __name__ == "__main__":
    initialize_database()