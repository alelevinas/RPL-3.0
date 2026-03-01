import logging
from typing import Annotated
from fastapi import Depends
from celery import Celery
from rpl_activities.src.config import env
from fastapi import HTTPException, status

class MQSender:
    def __init__(self):
        self.celery_app = Celery("rpl_runner", broker=env.QUEUE_URL)

    def send_submission(self, submission_id: int, language_with_version: str):
        message = f"{submission_id} {language_with_version}"
        try:
            # We use send_task because the consumer (runner) is in a different codebase/environment
            # The task name 'process_submission' must match @app.task(name='process_submission') in runner
            self.celery_app.send_task("process_submission", args=[message])
            logging.info(f"Successfully enqueued submission {submission_id} via Celery")
        except Exception as e:
            logging.error(f"Failed to enqueue submission {submission_id} via Celery: {e}")
            raise e

    def close(self):
        # Celery connection is managed by the app instance
        pass


def get_mq_sender():
    try:
        mq_sender = MQSender()
        yield mq_sender
    except Exception as e:
        logging.error(f"Failed to connect to MQ via Celery: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Message Queue service is currently unavailable. Wait a few seconds and try again."
        )


MQSenderDependency = Annotated[MQSender, Depends(get_mq_sender)]
