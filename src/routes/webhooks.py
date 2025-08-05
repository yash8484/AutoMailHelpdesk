from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from ..workers.email_processor import process_email_task

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class GmailWebhookPayload(BaseModel):
    message: Dict[str, Any]
    subscription: str


@router.post("/gmail")
async def gmail_webhook(payload: GmailWebhookPayload, background_tasks: BackgroundTasks):
    """
    Handle Gmail push notifications for new emails.
    """
    try:
        # TODO: Validate webhook signature/authentication
        
        # Extract message data
        message_data = payload.message.get("data", "")
        message_id = payload.message.get("messageId", "")
        
        if not message_data:
            raise HTTPException(status_code=400, detail="Invalid payload: missing message data")
        
        # Queue email processing task
        # TODO: Use Celery task queue instead of background tasks for production
        background_tasks.add_task(process_email_task, message_data, message_id)
        
        return {"status": "accepted", "message_id": message_id}
    
    except Exception as e:
        # TODO: Add proper logging and error handling
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.post("/manual-trigger")
async def manual_email_trigger(background_tasks: BackgroundTasks):
    """
    Manually trigger email processing (for testing/debugging).
    """
    try:
        # TODO: Add authentication/authorization for this endpoint
        
        # Trigger email polling and processing
        background_tasks.add_task(process_email_task, None, None)
        
        return {"status": "triggered"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual trigger failed: {str(e)}")


# TODO: Add more webhook endpoints as needed (e.g., Odoo webhooks, Slack webhooks)

