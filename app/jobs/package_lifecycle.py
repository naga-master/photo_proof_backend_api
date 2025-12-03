"""Background jobs for package lifecycle management (archival, retention, etc.)."""

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Project
from app.middleware.package_restrictions import (
    calculate_archival_date,
    calculate_retention_deadline,
    get_package_restrictions,
)

logger = logging.getLogger(__name__)


def process_archival_jobs():
    """
    Daily job to process project archival based on package restrictions.
    
    Finds projects that have reached their archival date and:
    1. Updates project status to 'archived'
    2. Optionally moves files to cold storage
    3. Sends notification to client
    
    Should be run as a daily cron job.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting archival job...")
        
        # Get all active projects with packages
        projects = db.query(Project).filter(
            Project.status.in_(['active', 'completed']),
            Project.package_id.isnot(None)
        ).all()
        
        archived_count = 0
        
        for project in projects:
            archival_date = calculate_archival_date(project.id, db)
            
            if archival_date and datetime.now() >= archival_date:
                # Archive the project
                logger.info(f"Archiving project {project.id}: {project.title}")
                
                project.status = 'archived'
                db.commit()
                
                archived_count += 1
                
                # TODO: Move files to cold storage
                # TODO: Send notification to client
        
        logger.info(f"Archival job completed. Archived {archived_count} projects.")
        
        return archived_count
        
    except Exception as e:
        logger.error(f"Error in archival job: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def process_retention_cleanup():
    """
    Weekly job to clean up projects past their retention period.
    
    Finds projects that have exceeded their retention period and:
    1. Sends final warning notification (if not already sent)
    2. Deletes project and associated files
    
    Should be run as a weekly cron job.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting retention cleanup job...")
        
        # Get all projects (including archived)
        projects = db.query(Project).filter(
            Project.package_id.isnot(None)
        ).all()
        
        deleted_count = 0
        warning_count = 0
        
        for project in projects:
            retention_deadline = calculate_retention_deadline(project.id, db)
            
            if retention_deadline:
                days_until_deletion = (retention_deadline - datetime.now()).days
                
                # Send warning 30 days before deletion
                if 0 < days_until_deletion <= 30:
                    logger.info(f"Sending retention warning for project {project.id}: {days_until_deletion} days left")
                    # TODO: Send warning notification
                    warning_count += 1
                
                # Delete if past deadline
                elif days_until_deletion <= 0:
                    logger.warning(f"Deleting project {project.id} due to retention period expiry")
                    
                    # TODO: Delete associated files from storage
                    # TODO: Send final notification
                    
                    db.delete(project)
                    db.commit()
                    
                    deleted_count += 1
        
        logger.info(f"Retention cleanup completed. Warnings: {warning_count}, Deleted: {deleted_count}")
        
        return {"warnings": warning_count, "deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error in retention cleanup job: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def send_lifecycle_notifications():
    """
    Daily job to send proactive notifications about upcoming deadlines.
    
    Sends notifications for:
    - Editing period ending soon
    - Archival approaching
    - Retention deadline approaching
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting lifecycle notifications job...")
        
        # TODO: Implement notification logic
        # - Find projects with deadlines in next 7/14/30 days
        # - Send email/WhatsApp notifications
        # - Track which notifications have been sent
        
        logger.info("Lifecycle notifications completed.")
        
    except Exception as e:
        logger.error(f"Error in lifecycle notifications job: {e}")
        raise
    finally:
        db.close()


# Cron job examples (for deployment):
# Daily archival: 0 2 * * * python -m app.jobs.package_lifecycle process_archival
# Weekly cleanup: 0 3 * * 0 python -m app.jobs.package_lifecycle process_retention
# Daily notifications: 0 9 * * * python -m app.jobs.package_lifecycle send_notifications
