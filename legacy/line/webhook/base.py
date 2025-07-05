from typing import Optional, Union

from line.domains import Bot
from organization.domains.organization import Organization
from packages.line.domains.event import (
    AccountLinkEvent,
    BeaconEvent,
    Event,
    FollowEvent,
    JoinEvent,
    LeaveEvent,
    MemberJoinedEvent,
    MemberLeftEvent,
    MessageEvent,
    PostbackEvent,
    UnfollowEvent,
    UnsendEvent,
    VideoPlayCompleteEvent,
)


class BaseWebhookHandler:
    TYPE_MAP = {
        "message": "message",
        "unsend": "unsend",
        "follow": "follow",
        "unfollow": "unfollow",
        "join": "join",
        "leave": "leave",
        "memberJoined": "member_joined",
        "memberLeft": "member_left",
        "postback": "postback",
        "beacon": "beacon",
        "accountLink": "account_link",
        "things": "things",
        "delivery": "delivery",
    }

    def __init__(
        self,
        bot: dict,
        event: dict,
        uuid: str,
        bot_instance: Optional[Bot] = None,
        event_instance: Optional[
            Union[
                Event,
                MessageEvent,
                UnsendEvent,
                FollowEvent,
                UnfollowEvent,
                JoinEvent,
                LeaveEvent,
                MemberJoinedEvent,
                MemberLeftEvent,
                PostbackEvent,
                VideoPlayCompleteEvent,
                BeaconEvent,
                AccountLinkEvent,
            ]
        ] = None,
        organization: Optional[Organization] = None,
    ):
        # TODO: implement Singleton pattern in webhook handlers
        self.bot = bot
        self.event = event
        self.bot_instance = bot_instance
        self.event_instance = event_instance
        self.organization = organization
        self.uuid = uuid
        self.mode = event.get("mode", "active")

    @property
    def is_channel_active(self) -> bool:
        # Channel state
        # "active": The channel is active. You can send a reply message or
        # push message, etc. from the bot server that received this webhook event.
        # "standby": The channel is waiting. When the channel state is standby,
        # the webhook event won't contain a reply token to send reply message.
        # Ref: https://developers.line.biz/en/reference/messaging-api/#common-properties
        return self.mode == "active"

    def message(self, process_data: dict) -> dict:
        return process_data

    def unsend(self, process_data: dict) -> dict:
        return process_data

    def follow(self, process_data: dict) -> dict:
        return process_data

    def unfollow(self, process_data: dict) -> dict:
        return process_data

    def join(self, process_data: dict) -> dict:
        return process_data

    def leave(self, process_data: dict) -> dict:
        return process_data

    def member_joined(self, process_data: dict) -> dict:
        return process_data

    def member_left(self, process_data: dict) -> dict:
        return process_data

    def postback(self, process_data: dict) -> dict:
        return process_data

    def beacon(self, process_data: dict) -> dict:
        return process_data

    def account_link(self, process_data: dict) -> dict:
        return process_data

    def things(self, process_data: dict) -> dict:
        return process_data

    def delivery(self, process_data: dict) -> dict:
        return process_data

    def add_messages(
        self,
        process_data: dict,
        messages: list,
        type: str,
        ref_id: int,
        insert: bool = False,
    ) -> dict:
        message_infos = []
        if insert:
            process_data["messages"] = messages.extend(process_data["messages"])
            for i in range(len(messages)):
                message_infos.append({"type": type, "ref_id": ref_id})
            process_data["message_infos"] = message_infos.extend(
                process_data["message_infos"]
            )
        else:
            process_data["messages"].extend(messages)
            for i in range(len(messages)):
                message_infos.append({"type": type, "ref_id": ref_id})
            process_data["message_infos"].extend(message_infos)
        return process_data
