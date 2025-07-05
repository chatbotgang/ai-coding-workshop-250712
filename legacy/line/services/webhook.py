import importlib
import logging
from typing import Optional
from uuid import uuid4


from line.constants import BotModule
from line.domains import Bot
from line.repositories import bot_repository
from line.repositories.webhook import WebhookRepository
from line.webhook.base import BaseWebhookHandler
from organization.domains.organization import Organization
from organization.repositories import OrganizationRepository

logger = logging.getLogger("rubato")


class ProcessLineWebhookService:
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        webhook_repository: WebhookRepository,
    ) -> None:
        self.organization_repository = organization_repository
        self.webhook_repository = webhook_repository

    def execute(self, *, bot_dict: dict, event_data: dict) -> None:
        # TODO: Remove workaround after bot_dict data structure is matched with Bot domain
        # bot: Bot = Bot.parse_obj(obj=bot_dict)
        bot: Bot = bot_repository.get_bot(bot_id=bot_dict["id"])

        try:
            event: Event = Event.parse_event(event=event_data)
        except ValueError as exc:
            logger.exception(
                {
                    "message": f"[{__class__.__name__}] Parse event failed",
                    "error": str(exc),
                }
            )
            return None

        # Check Idempotency
        if self.webhook_repository.is_line_webhook_event_executed(
            webhook_event_id=event.webhook_event_id
        ):
            return None
        else:
            self.webhook_repository.set_line_webhook_event_executed(
                webhook_event_id=event.webhook_event_id
            )

        organization: Optional[Organization] = (
            self.organization_repository.get_organization_by_id(
                organization_id=bot.organization_id
            )
        )
        if organization is None:
            logger.warning(
                {
                    "message": f"[{__class__.__name__}] Organization not found",
                    "organization_id": bot.organization_id,
                }
            )
            return None

        logger.info(
            {
                "message": f"[{__class__.__name__}] Processed LINE webhook event",
                "bot_id": bot.id,
                "webhook_event_id": event.webhook_event_id,
                "event": event.dict(),
            }
        )

        uuid: str = event.webhook_event_id or uuid4().hex
        event_attr = BaseWebhookHandler.TYPE_MAP.get(event.type)
        if not event_attr:
            logger.warning(
                {
                    "message": f"[{__class__.__name__}] Event type {event.type} is not supported",
                    "bot_id": bot.id,
                    "webhook_event_id": event.webhook_event_id,
                    "event": event.dict(),
                }
            )
            return None

        module_list = [
            "trigger_v2",
        ]
        # Extend the module list with the modules set in the database
        if bot_dict["module"]:
            bot_modules = bot_dict["module"].split(",")
            if BotModule.PNP.value in bot_modules:
                module_list.insert(0, BotModule.PNP.value)
                bot_modules.remove(BotModule.PNP.value)
            module_list += bot_modules  # Note that module list order matters because of process_data's "continue_process" & "skip_process" mechanisms.
        module_list.append("message")

        # Initialize process_data
        process_data = {
            "messages": [],
            "message_infos": [],
            "continue_process": True,
            "skip_process": [],
            "auto_reply_triggered": False,
        }
        for module_name in module_list:
            if module_name in process_data["skip_process"]:
                logger.info(
                    {
                        "message": f"[{__class__.__name__}] Webhook module execution skipped",
                        "webhook_module": module_name,
                        "bot_id": bot.id,
                        "webhook_event_id": event.webhook_event_id,
                        "event": event.dict(),
                    }
                )
                continue

            logger.info(
                {
                    "message": f"[{__class__.__name__}] Webhook module execution started",
                    "webhook_module": module_name,
                    "bot_id": bot.id,
                    "webhook_event_id": event.webhook_event_id,
                    "event": event.dict(),
                }
            )
            try:
                module = importlib.import_module(f"line.webhook.{module_name}")

                # TODO: Waiting for all modules to be changed to use instance and remove the original dict data
                handler = getattr(
                    module.Handler(
                        bot=bot_dict,
                        event=event.raw_data,
                        uuid=uuid,
                        bot_instance=bot,
                        event_instance=event,
                        organization=organization,
                    ),
                    event_attr,
                )
                process_data = handler(process_data)
                logger.info(
                    {
                        "message": f"[{__class__.__name__}] Webhook module execution completed",
                        "webhook_module": module_name,
                        "bot_id": bot.id,
                        "webhook_event_id": event.webhook_event_id,
                        "event": event.dict(),
                    }
                )

                if not process_data["continue_process"]:
                    logger.info(
                        {
                            "message": f"[{__class__.__name__}] Webhook module execution stopped",
                            "webhook_module": module_name,
                            "bot_id": bot.id,
                            "webhook_event_id": event.webhook_event_id,
                            "event": event.dict(),
                        }
                    )
                    break
            except Exception as exc:
                logger.exception(
                    {
                        "message": f"[{__class__.__name__}] Webhook module execution failed",
                        "webhook_module": module_name,
                        "bot_id": bot.id,
                        "webhook_event_id": event.webhook_event_id,
                        "event": event.dict(),
                        "error": str(exc),
                    }
                )
                continue
