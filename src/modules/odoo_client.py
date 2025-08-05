import logging
from typing import Dict, Any, Optional, List
import xmlrpc.client
from tenacity import retry, stop_after_attempt, wait_exponential
from aiobreaker import CircuitBreaker
from ..settings import settings

logger = logging.getLogger(__name__)


class OdooClient:
    """
    Odoo API client for ticket management.
    """
    
    def __init__(self):
        self.url = settings.ODOO_URL
        self.database = settings.ODOO_DATABASE
        self.username = settings.ODOO_USERNAME
        self.password = settings.ODOO_PASSWORD
        
        # Initialize XML-RPC connections
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # Authenticate
        self.uid = self._authenticate()
        
        # Circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
    
    def _authenticate(self) -> int:
        """
        Authenticate with Odoo and return user ID.
        """
        try:
            uid = self.common.authenticate(
                self.database,
                self.username,
                self.password,
                {}
            )
            if not uid:
                raise Exception("Authentication failed")
            
            logger.info(f"Authenticated with Odoo as user {uid}")
            return uid
        
        except Exception as e:
            logger.error(f"Odoo authentication failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def create_ticket(self, parsed_email: Dict[str, Any], intent_result: Dict[str, Any]) -> str:
        """
        Create a new helpdesk ticket in Odoo.
        """
        try:
                # TODO: Map email data to Odoo helpdesk ticket fields
                ticket_data = {
                    'name': parsed_email['subject'],
                    'description': parsed_email['body'],
                    'partner_email': parsed_email['sender'],
                    'priority': self._get_priority_from_intent(intent_result['intent']),
                    'team_id': self._get_team_from_intent(intent_result['intent']),
                    'tag_ids': self._get_tags_from_intent(intent_result),
                    # Custom fields for AI processing
                    'x_email_id': parsed_email['id'],
                    'x_thread_id': parsed_email['thread_id'],
                    'x_intent': intent_result['intent'],
                    'x_entities': str(intent_result.get('entities', {})),
                    'x_confidence': intent_result.get('confidence', 0.0),
                }
                
                # Create ticket
                ticket_id = self.models.execute_kw(
                    self.database, self.uid, self.password,
                    'helpdesk.ticket', 'create',
                    [ticket_data]
                )
                
                logger.info(f"Created Odoo ticket {ticket_id} for email {parsed_email['id']}")
                return str(ticket_id)
        
        except Exception as e:
            logger.error(f"Error creating Odoo ticket: {e}")
            raise
    
    def append_to_ticket(self, ticket_id: str, parsed_email: Dict[str, Any], intent_result: Dict[str, Any]):
        """
        Append new message to existing ticket.
        """
        try:
                # TODO: Add message to ticket
                message_data = {
                    'res_id': int(ticket_id),
                    'model': 'helpdesk.ticket',
                    'message_type': 'email',
                    'subtype_id': self._get_message_subtype_id(),
                    'body': parsed_email['body'],
                    'email_from': parsed_email['sender'],
                    'subject': parsed_email['subject'],
                    # Custom fields
                    'x_email_id': parsed_email['id'],
                    'x_intent': intent_result['intent'],
                    'x_entities': str(intent_result.get('entities', {})),
                }
                
                message_id = self.models.execute_kw(
                    self.database, self.uid, self.password,
                    'mail.message', 'create',
                    [message_data]
                )
                
                # Update ticket with latest intent
                self.models.execute_kw(
                    self.database, self.uid, self.password,
                    'helpdesk.ticket', 'write',
                    [[int(ticket_id)], {
                        'x_last_intent': intent_result['intent'],
                        'x_last_entities': str(intent_result.get('entities', {})),
                    }]
                )
                
                logger.info(f"Appended message {message_id} to ticket {ticket_id}")
        
        except Exception as e:
            logger.error(f"Error appending to ticket {ticket_id}: {e}")
            raise
    
    def get_ticket_last_intent(self, ticket_id: str) -> Optional[str]:
        """
        Get the last known intent for a ticket.
        """
        try:
                tickets = self.models.execute_kw(
                    self.database, self.uid, self.password,
                    'helpdesk.ticket', 'read',
                    [[int(ticket_id)], ['x_last_intent']]
                )
                
                if tickets:
                    return tickets[0].get('x_last_intent')
                return None
        
        except Exception as e:
            logger.error(f"Error getting last intent for ticket {ticket_id}: {e}")
            return None
    
    def get_ticket_history(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a ticket.
        """
        try:
            async with self.circuit_breaker:
                # TODO: Get all messages for the ticket
                messages = self.models.execute_kw(
                    self.database, self.uid, self.password,
                    'mail.message', 'search_read',
                    [[['res_id', '=', int(ticket_id)], ['model', '=', 'helpdesk.ticket']]],
                    {'fields': ['date', 'body', 'email_from', 'x_intent', 'x_entities']}
                )
                
                return messages
        
        except Exception as e:
            logger.error(f"Error getting ticket history for {ticket_id}: {e}")
            return []
    
    def _get_priority_from_intent(self, intent: str) -> str:
        """
        Map intent to ticket priority.
        """
        priority_map = {
            'urgent_human': '3',  # High
            'password_update': '2',  # Medium
            'bank_statement': '1',  # Low
            'general_query': '1',  # Low
            'fallback_human': '2',  # Medium
        }
        return priority_map.get(intent, '1')
    
    def _get_team_from_intent(self, intent: str) -> Optional[int]:
        """
        Map intent to helpdesk team.
        """
        # TODO: Configure team IDs based on your Odoo setup
        team_map = {
            'urgent_human': 1,  # Escalation team
            'password_update': 2,  # IT support team
            'bank_statement': 3,  # Finance team
            'general_query': 4,  # General support team
            'fallback_human': 1,  # Escalation team
        }
        return team_map.get(intent)
    
    def _get_tags_from_intent(self, intent_result: Dict[str, Any]) -> List[int]:
        """
        Map intent and entities to ticket tags.
        """
        # TODO: Configure tag IDs based on your Odoo setup
        tags = []
        intent = intent_result['intent']
        
        # Add intent-based tags
        intent_tags = {
            'bank_statement': [1],  # Tag ID for bank statements
            'password_update': [2],  # Tag ID for password updates
            'general_query': [3],  # Tag ID for general queries
            'urgent_human': [4],  # Tag ID for urgent requests
            'fallback_human': [5],  # Tag ID for fallback/unknown
        }
        
        tags.extend(intent_tags.get(intent, []))
        
        # Add entity-based tags
        entities = intent_result.get('entities', {})
        if entities.get('months'):
            tags.append(6)  # Tag for time-based requests
        
        return tags
    
    def _get_message_subtype_id(self) -> int:
        """
        Get the message subtype ID for email messages.
        """
        # TODO: Configure based on your Odoo setup
        return 1  # Default email subtype
    
    # TODO: Add more methods for ticket management (update, close, etc.)

