import time
from loguru import logger
from tasks.celery_app import celery_app


@celery_app.task(name="send_email_task")
def send_email_task(email: str, subject: str, body: str) -> bool:
    """
    Simulated background task to send an email.
    """
    logger.info(f"Starting email dispatch task to: {email}")
    # Simulate network latency
    time.sleep(3)
    logger.info(f"Email successfully sent to {email} with subject: '{subject}'")
    return True


@celery_app.task(name="generate_report_task")
def generate_report_task(user_id: str) -> str:
    """
    Simulated background task to generate a complex PDF/CSV report.
    """
    logger.info(f"Starting report generation task for user ID: {user_id}")
    # Simulate high CPU/IO processing
    time.sleep(5)
    report_url = f"https://s3.amazonaws.com/reports/user-{user_id}-report.pdf"
    logger.info(f"Report generated successfully. URL: {report_url}")
    return report_url
