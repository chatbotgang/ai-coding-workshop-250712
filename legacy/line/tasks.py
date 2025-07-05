from celery.utils.log import get_task_logger

from line.repositories import (
    webhook_repository,
)
from organization.repositories import organization_repository
from rubato.celery import (
    QUEUE_LINE_WEBHOOK,
    app,
)
from line.services.webhook import ProcessLineWebhookService


logger = get_task_logger("rubato_celery")

process_line_webhook_service = ProcessLineWebhookService(
    organization_repository=organization_repository,
    webhook_repository=webhook_repository,
)


@app.task(bind=True, queue=QUEUE_LINE_WEBHOOK)
def webhook_event_handler(self, *, bot: dict, event: dict):
    try:
        process_line_webhook_service.execute(bot_dict=bot, event_data=event)
    except Exception as exc:
        logger.exception(
            {
                "message": "[webhook_event_handler] LINE webhook event processing failed",
                "bot_id": bot["id"],
                "event": event,
                "exc": exc,
            }
        )
    return f"[webhook_event_handler] {bot}|{event}"
