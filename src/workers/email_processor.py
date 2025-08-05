import asyncio
import logging
from typing import Optional, Dict, Any
from celery import Celery
from ..modules.gmail_client import GmailClient
from ..modules.odoo_client import OdooClient
from ..modules.llm_engine import LLMEngine
from ..modules.rag_store import RAGStore
from ..modules.email_drafts import EmailDrafts
from ..modules.escalation import EscalationHandler
from ..memory.ticket_memory import TicketMemory
from ..settings import settings

# Initialize Celery app
celery_app = Celery(
    "email_processor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "email_processor.process_email_task": {"queue": "email_processing"},
        "email_processor.process_intent_task": {"queue": "intent_processing"},
    },
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=settings.MAX_RETRIES)
def process_email_task(self, message_data: Optional[str], message_id: Optional[str]):
    """
    Main email processing task.
    """
    try:
        # TODO: Initialize clients and dependencies
        gmail_client = GmailClient()
        odoo_client = OdooClient()
        llm_engine = LLMEngine()
        rag_store = RAGStore()
        email_drafts = EmailDrafts()
        escalation_handler = EscalationHandler()
        ticket_memory = TicketMemory()
        
        # TODO: If message_data is None, poll for new emails
        if message_data is None:
            # Manual trigger - poll for new emails
            emails = gmail_client.poll_new_emails()
        else:
            # Webhook trigger - process specific email
            emails = [gmail_client.get_email_by_message_id(message_id)]
        
        for email in emails:
            # TODO: Check for deduplication
            if gmail_client.is_email_processed(email["id"]):
                logger.info(f"Email {email['id']} already processed, skipping")
                continue
            
            # TODO: Parse email content
            parsed_email = gmail_client.parse_email(email)
            
            # TODO: Extract ticket ID from email (if present)
            ticket_id = extract_ticket_id(parsed_email["subject"], parsed_email["body"])
            
            # TODO: Classify intent using LLM
            intent_result = llm_engine.classify_intent(
                parsed_email["body"],
                parsed_email["sender"],
                ticket_memory.get_conversation_history(ticket_id) if ticket_id else None
            )
            
            # TODO: Handle ticket management
            if ticket_id:
                # Check if intent changed
                last_intent = odoo_client.get_ticket_last_intent(ticket_id)
                if last_intent != intent_result["intent"]:
                    # Create new ticket for different intent
                    ticket_id = odoo_client.create_ticket(parsed_email, intent_result)
                else:
                    # Append to existing ticket
                    odoo_client.append_to_ticket(ticket_id, parsed_email, intent_result)
            else:
                # Create new ticket
                ticket_id = odoo_client.create_ticket(parsed_email, intent_result)
            
            # TODO: Update ticket memory
            ticket_memory.update_conversation(ticket_id, parsed_email, intent_result)
            
            # TODO: Process based on intent
            response = asyncio.run(process_intent(
                intent_result,
                parsed_email,
                ticket_id,
                llm_engine,
                rag_store,
                escalation_handler
            ))
            
            # TODO: Create Gmail draft
            if response:
                asyncio.run(email_drafts.create_draft(
                    to_email=parsed_email["sender"],
                    subject=f"Re: {parsed_email['subject']}",
                    body=response["body"],
                    ticket_id=ticket_id,
                    metadata={"attachments": response.get("attachments", [])}
                ))
            
            # TODO: Mark email as processed
            gmail_client.mark_email_processed(email["id"])
            
            logger.info(f"Successfully processed email {email['id']} for ticket {ticket_id}")
    
    except Exception as exc:
        logger.error(f"Email processing failed: {str(exc)}")
        # TODO: Implement retry logic with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def process_intent(
    intent_result: Dict[str, Any],
    parsed_email: Dict[str, Any],
    ticket_id: str,
    llm_engine: LLMEngine,
    rag_store: RAGStore,
    escalation_handler: EscalationHandler
) -> Optional[Dict[str, Any]]:
    """
    Process email based on classified intent.
    """
    intent = intent_result["intent"]
    entities = intent_result.get("entities", {})
    
    try:
        if intent == "bank_statement":
            # TODO: Import and use bank statement handler
            from ..modules.handlers.bank_statement_handler import BankStatementHandler
            handler = BankStatementHandler()
            return await handler.handle(entities, parsed_email, ticket_id)
        
        elif intent == "password_update":
            # TODO: Import and use password update handler
            from ..modules.handlers.password_update_handler import PasswordUpdateHandler
            handler = PasswordUpdateHandler()
            return await handler.handle(entities, parsed_email, ticket_id)
        
        elif intent == "general_query":
            # TODO: Import and use general query handler
            from ..modules.handlers.general_query_handler import GeneralQueryHandler
            handler = GeneralQueryHandler(llm_engine, rag_store)
            return await handler.handle(entities, parsed_email, ticket_id)
        
        elif intent in ["urgent_human", "fallback_human"]:
            # TODO: Escalate to human
            await escalation_handler.escalate(parsed_email, ticket_id, intent)
            return {
                "body": "Thank you for contacting us. Your request has been escalated to a human agent who will respond shortly.",
                "attachments": []
            }
        
        else:
            # TODO: Handle unknown intent
            logger.warning(f"Unknown intent: {intent}")
            await escalation_handler.escalate(parsed_email, ticket_id, "unknown_intent")
            return {
                "body": "Thank you for your message. We're reviewing your request and will respond soon.",
                "attachments": []
            }
    
    except Exception as e:
        logger.error(f"Intent processing failed for {intent}: {str(e)}")
        await escalation_handler.escalate(parsed_email, ticket_id, f"processing_error_{intent}")
        return None


def extract_ticket_id(subject: str, body: str) -> Optional[str]:
    """
    Extract ticket ID from email subject or body using regex.
    """
    import re
    
    # TODO: Implement regex patterns to extract ticket IDs
    # Common patterns: [TICKET-12345], #12345, Ticket: 12345, etc.
    patterns = [
        r'\[TICKET-(\d+)\]',
        r'#(\d+)',
        r'Ticket:\s*(\d+)',
        r'ID:\s*(\d+)',
    ]
    
    text = f"{subject} {body}"
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


# TODO: Add more utility functions as needed

