"""Tests for Phase 26 Communication & Social Automation 2.0."""

from __future__ import annotations

import asyncio

from communications.action_planner import CommunicationActionPlanner
from communications.contacts import ContactManager, contact_manager
from communications.email_intelligence import EmailIntelligence
from communications.inbox import UnifiedInbox
from communications.intent_router import CommunicationIntent, IntentRouter
from communications.manager import CommunicationManager, communication_manager
from communications.models import (
    Attachment,
    CallRecord,
    Conversation,
    MessageImportance,
    MessageStatus,
    ProviderType,
    ScheduledMessage,
    UnifiedMessage,
)
from communications.normalizer import MessageNormalizer
from communications.notifications import CommunicationNotificationManager
from communications.queue import MessageQueue, QueuedMessage
from communications.scheduler import ScheduledMessageManager


def test_unified_message_defaults():
    msg = UnifiedMessage()
    assert msg.provider == ""
    assert msg.status == MessageStatus.PENDING
    assert msg.importance == MessageImportance.UNKNOWN

def test_unified_message_to_dict():
    msg = UnifiedMessage(provider="email", sender="ali@example.com", text="Hello")
    d = msg.to_dict()
    assert d["provider"] == "email"
    assert d["sender"] == "ali@example.com"
    assert "message_id" in d

def test_conversation_defaults():
    conv = Conversation()
    assert conv.provider == ""
    assert conv.unread_count == 0

def test_contact_defaults():
    contact = ContactManager()
    assert contact.list_all() == []

def test_contact_add_resolve():
    from communications.models import Contact
    cm = ContactManager()
    cm.add_contact(Contact(name="Ali", aliases=["brother"], tags=["family"]))
    matches = cm.resolve("Ali")
    assert len(matches) == 1
    assert matches[0].name == "Ali"
    matches2 = cm.resolve("brother")
    assert len(matches2) == 1

def test_message_normalizer():
    normalizer = MessageNormalizer()
    raw = {"sender": "Ali", "text": "Hello", "conversation_id": "conv-1", "unread": True}
    msg = normalizer.normalize(raw, "whatsapp", "messaging")
    assert msg.sender == "Ali"
    assert msg.text == "Hello"
    assert msg.unread is True
    assert msg.provider == "whatsapp"

def test_message_normalizer_alt_fields():
    normalizer = MessageNormalizer()
    raw = {"from": "Ali", "content": "Hello", "id": "msg-1"}
    msg = normalizer.normalize(raw, "telegram", "messaging")
    assert msg.sender == "Ali"
    assert msg.text == "Hello"
    assert msg.message_id == "msg-1"

def test_intent_router():
    router = IntentRouter()
    intent = router.route("Check my messages")
    assert intent.intent == "read_messages"
    intent2 = router.route("Send a message to Ali")
    assert intent2.intent == "send_message"
    assert intent2.target == "Ali"

def test_intent_router_email():
    router = IntentRouter()
    intent = router.route("Check my email")
    assert intent.intent == "read_email"

def test_intent_router_call():
    router = IntentRouter()
    intent = router.route("Call Ali")
    assert intent.intent == "make_call"
    assert intent.target == "Ali"

def test_action_planner():
    cm = contact_manager
    planner = CommunicationActionPlanner(communication_manager, cm)
    intent = CommunicationIntent(intent="read_messages", provider=None, target=None)
    actions = planner.plan(intent)
    assert len(actions) == 1
    assert actions[0].action_type == "read_messages"

def test_action_planner_call():
    cm = contact_manager
    planner = CommunicationActionPlanner(communication_manager, cm)
    intent = CommunicationIntent(intent="make_call", provider="phone", target="Ali")
    actions = planner.plan(intent)
    assert len(actions) == 1
    assert actions[0].action_type == "make_call"

def test_communication_manager_defaults():
    mgr = CommunicationManager()
    assert mgr.enabled is False

def test_communication_manager_list_providers():
    from communications.email_provider import EmailProvider
    from communications.messaging_provider import MessagingProvider
    mgr = CommunicationManager()
    mgr.register_provider("email", EmailProvider())
    mgr.register_provider("messaging", MessagingProvider())
    providers = mgr.list_providers()
    assert len(providers) == 2

def test_notification_manager():
    nm = CommunicationNotificationManager()
    assert nm.enabled is True
    assert nm.preview_enabled is True
    assert nm.read_aloud is False

def test_message_queue():
    mq = MessageQueue()
    msg = QueuedMessage(provider="email", recipient="Ali", text="Hello")
    mq.enqueue(msg)
    assert len(mq.list_pending()) == 1
    found = mq.get(msg.queue_id)
    assert found is not None
    assert found.status == "pending"

def test_scheduled_manager():
    sm = ScheduledMessageManager()
    msg = ScheduledMessage(provider="email", recipient="Ali", message="Hello", schedule_time="2026-08-17T20:00:00")
    sm.schedule(msg)
    assert len(sm.list_pending()) == 1
    assert sm.cancel(msg.schedule_id) is True
    assert len(sm.list_pending()) == 0

def test_email_intelligence_classify():
    ei = EmailIntelligence()
    important = ei.classify({"sender": "github", "subject": "Important", "text": "Review"})
    assert important == MessageImportance.IMPORTANT
    spam = ei.classify({"sender": "promo", "subject": "Free money", "text": "Unsubscribe"})
    assert spam == MessageImportance.SPAM

def test_email_intelligence_summarize():
    ei = EmailIntelligence()
    result = ei.summarize({"sender": "Ali", "subject": "Meeting", "text": "Let's meet", "timestamp": "2026-08-17"})
    assert result["sender"] == "Ali"
    assert result["importance"] == MessageImportance.NORMAL

def test_unified_inbox():
    ui = UnifiedInbox(communication_manager)
    result = asyncio.run(ui.get_inbox())
    assert result["success"] is False

def test_attachment_defaults():
    att = Attachment()
    assert att.filename == ""
    assert att.status == MessageStatus.PENDING

def test_call_record_defaults():
    call = CallRecord()
    assert call.status == "idle"
    assert call.duration == 0

def test_provider_type_enum():
    assert ProviderType.EMAIL == "email"
    assert ProviderType.MESSAGING == "messaging"
    assert ProviderType.BROWSER == "browser"
