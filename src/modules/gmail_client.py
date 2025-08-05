import asyncio
import logging
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential
from aiobreaker import CircuitBreaker
from ..settings import settings

logger = logging.getLogger(__name__)


class GmailClient:
    """
    Gmail API client for email ingestion and management.
    """
    
    def __init__(self):
        self.credentials = self._get_credentials()
        self.service = build('gmail', 'v1', credentials=self.credentials)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        # TODO: Initialize processed emails cache/database
        self.processed_emails = set()  # Replace with persistent storage
    
    def _get_credentials(self) -> Credentials:
        """
        Get Gmail API credentials from environment variables.
        """
        # TODO: Implement OAuth2 credential management
        creds = Credentials(
            token=settings.GMAIL_ACCESS_TOKEN,
            refresh_token=settings.GMAIL_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
        )
        return creds
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def poll_new_emails(self) -> List[Dict[str, Any]]:
        """
        Poll Gmail for new emails.
        """
        try:
            # TODO: Implement rate limiting
            async with self.circuit_breaker:
                # Get unread emails
                results = self.service.users().messages().list(
                    userId='me',
                    q='is:unread',
                    maxResults=50
                ).execute()
                
                messages = results.get('messages', [])
                emails = []
                
                for message in messages:
                    email_data = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    emails.append(email_data)
                
                logger.info(f"Retrieved {len(emails)} new emails")
                return emails
        
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error polling emails: {e}")
            raise
    
    def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific email by message ID.
        """
        try:
            email_data = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            return email_data
        except HttpError as e:
            logger.error(f"Error getting email {message_id}: {e}")
            raise
    
    def parse_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse email data to extract relevant information.
        """
        try:
            headers = email_data['payload'].get('headers', [])
            
            # Extract headers
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(email_data['payload'])
            
            # Extract attachments
            attachments = self._extract_attachments(email_data['payload'])
            
            parsed = {
                'id': email_data['id'],
                'thread_id': email_data['threadId'],
                'sender': sender,
                'subject': subject,
                'date': date,
                'body': body,
                'attachments': attachments,
                'raw_data': email_data
            }
            
            logger.debug(f"Parsed email {email_data['id']}: {subject}")
            return parsed
        
        except Exception as e:
            logger.error(f"Error parsing email {email_data.get('id', 'unknown')}: {e}")
            raise
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from payload.
        """
        # TODO: Handle multipart messages, HTML/text content, etc.
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        import base64
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    import base64
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def _extract_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract attachment information from payload.
        """
        # TODO: Implement attachment extraction
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'mime_type': part['mimeType'],
                        'size': part['body'].get('size', 0),
                        'attachment_id': part['body'].get('attachmentId')
                    })
        
        return attachments
    
    def is_email_processed(self, email_id: str) -> bool:
        """
        Check if email has already been processed.
        """
        # TODO: Check against persistent storage (database)
        return email_id in self.processed_emails
    
    def mark_email_processed(self, email_id: str):
        """
        Mark email as processed.
        """
        # TODO: Store in persistent storage (database)
        self.processed_emails.add(email_id)
        logger.debug(f"Marked email {email_id} as processed")
    
    def mark_as_read(self, email_id: str):
        """
        Mark email as read in Gmail.
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.debug(f"Marked email {email_id} as read")
        except HttpError as e:
            logger.error(f"Error marking email {email_id} as read: {e}")
    
    # TODO: Add methods for email labeling, archiving, etc.

