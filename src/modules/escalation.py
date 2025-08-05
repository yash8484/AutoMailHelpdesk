"""
Escalation Handler Module

Manages ticket escalations and routing to appropriate support levels.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """Escalation levels for tickets."""
    LEVEL_1 = "level_1"  # Basic support
    LEVEL_2 = "level_2"  # Technical support
    LEVEL_3 = "level_3"  # Senior support
    URGENT = "urgent"    # Immediate attention
    MANAGER = "manager"  # Management escalation


class EscalationReason(Enum):
    """Reasons for escalation."""
    RESPONSE_TIME = "response_time"
    COMPLEXITY = "complexity"
    CUSTOMER_URGENCY = "customer_urgency"
    TECHNICAL_DIFFICULTY = "technical_difficulty"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    BUSINESS_IMPACT = "business_impact"


class EscalationHandler:
    """
    Handles ticket escalations and routing logic.
    """
    
    def __init__(self):
        self.escalation_rules = {
            EscalationLevel.LEVEL_1: {
                "max_response_time": timedelta(hours=4),
                "max_resolution_time": timedelta(days=1),
                "auto_escalate": True
            },
            EscalationLevel.LEVEL_2: {
                "max_response_time": timedelta(hours=2),
                "max_resolution_time": timedelta(hours=8),
                "auto_escalate": True
            },
            EscalationLevel.LEVEL_3: {
                "max_response_time": timedelta(hours=1),
                "max_resolution_time": timedelta(hours=4),
                "auto_escalate": True
            },
            EscalationLevel.URGENT: {
                "max_response_time": timedelta(minutes=30),
                "max_resolution_time": timedelta(hours=2),
                "auto_escalate": True
            },
            EscalationLevel.MANAGER: {
                "max_response_time": timedelta(minutes=15),
                "max_resolution_time": timedelta(hours=1),
                "auto_escalate": False
            }
        }
    
    async def check_escalation_needed(
        self,
        ticket_data: Dict[str, Any],
        current_level: EscalationLevel
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a ticket needs to be escalated.
        
        Args:
            ticket_data: Current ticket information
            current_level: Current escalation level
            
        Returns:
            Escalation details if needed, None otherwise
        """
        try:
            # Check response time
            if await self._check_response_time_escalation(ticket_data, current_level):
                return {
                    "reason": EscalationReason.RESPONSE_TIME,
                    "new_level": self._get_next_level(current_level),
                    "details": "Response time exceeded"
                }
            
            # Check customer urgency
            if await self._check_urgency_escalation(ticket_data):
                return {
                    "reason": EscalationReason.CUSTOMER_URGENCY,
                    "new_level": EscalationLevel.URGENT,
                    "details": "Customer marked as urgent"
                }
            
            # Check complexity
            if await self._check_complexity_escalation(ticket_data, current_level):
                return {
                    "reason": EscalationReason.COMPLEXITY,
                    "new_level": self._get_next_level(current_level),
                    "details": "Ticket complexity requires escalation"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking escalation: {e}")
            return None
    
    async def escalate_ticket(
        self,
        ticket_id: str,
        escalation_data: Dict[str, Any],
        odoo_client
    ) -> bool:
        """
        Escalate a ticket to the next level.
        
        Args:
            ticket_id: Ticket identifier
            escalation_data: Escalation information
            odoo_client: Odoo client instance
            
        Returns:
            True if escalated successfully
        """
        try:
            new_level = escalation_data["new_level"]
            reason = escalation_data["reason"]
            
            # Update ticket in Odoo
            update_data = {
                "escalation_level": new_level.value,
                "escalation_reason": reason.value,
                "escalated_at": datetime.now().isoformat(),
                "escalation_details": escalation_data.get("details", "")
            }
            
            success = await odoo_client.update_ticket(ticket_id, update_data)
            
            if success:
                logger.info(f"Escalated ticket {ticket_id} to {new_level.value}")
                
                # Send notification
                await self._send_escalation_notification(ticket_id, escalation_data)
                
                return True
            else:
                logger.error(f"Failed to escalate ticket {ticket_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error escalating ticket {ticket_id}: {e}")
            return False
    
    async def get_escalation_history(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Get escalation history for a ticket.
        
        Args:
            ticket_id: Ticket identifier
            
        Returns:
            List of escalation events
        """
        # TODO: Implement database query for escalation history
        return []
    
    async def _check_response_time_escalation(
        self,
        ticket_data: Dict[str, Any],
        current_level: EscalationLevel
    ) -> bool:
        """Check if ticket should be escalated due to response time."""
        try:
            last_update = ticket_data.get("last_update")
            if not last_update:
                return False
            
            last_update_time = datetime.fromisoformat(last_update)
            max_response_time = self.escalation_rules[current_level]["max_response_time"]
            
            return datetime.now() - last_update_time > max_response_time
            
        except Exception as e:
            logger.error(f"Error checking response time escalation: {e}")
            return False
    
    async def _check_urgency_escalation(self, ticket_data: Dict[str, Any]) -> bool:
        """Check if ticket should be escalated due to customer urgency."""
        try:
            priority = ticket_data.get("priority", "normal")
            return priority in ["high", "urgent", "critical"]
            
        except Exception as e:
            logger.error(f"Error checking urgency escalation: {e}")
            return False
    
    async def _check_complexity_escalation(
        self,
        ticket_data: Dict[str, Any],
        current_level: EscalationLevel
    ) -> bool:
        """Check if ticket should be escalated due to complexity."""
        try:
            # Check number of interactions
            interaction_count = ticket_data.get("interaction_count", 0)
            if interaction_count > 5 and current_level == EscalationLevel.LEVEL_1:
                return True
            
            # Check if technical keywords are present
            technical_keywords = ["error", "bug", "crash", "broken", "not working"]
            description = ticket_data.get("description", "").lower()
            
            if any(keyword in description for keyword in technical_keywords):
                if current_level == EscalationLevel.LEVEL_1:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking complexity escalation: {e}")
            return False
    
    def _get_next_level(self, current_level: EscalationLevel) -> EscalationLevel:
        """Get the next escalation level."""
        level_sequence = [
            EscalationLevel.LEVEL_1,
            EscalationLevel.LEVEL_2,
            EscalationLevel.LEVEL_3,
            EscalationLevel.MANAGER
        ]
        
        try:
            current_index = level_sequence.index(current_level)
            if current_index < len(level_sequence) - 1:
                return level_sequence[current_index + 1]
            else:
                return EscalationLevel.MANAGER
        except ValueError:
            return EscalationLevel.LEVEL_2
    
    async def _send_escalation_notification(
        self,
        ticket_id: str,
        escalation_data: Dict[str, Any]
    ) -> None:
        """Send notification about escalation."""
        try:
            # TODO: Implement notification logic (Slack, email, etc.)
            logger.info(f"Escalation notification sent for ticket {ticket_id}")
            
        except Exception as e:
            logger.error(f"Error sending escalation notification: {e}")
    
    async def get_escalation_metrics(self) -> Dict[str, Any]:
        """
        Get escalation metrics and statistics.
        
        Returns:
            Dictionary with escalation metrics
        """
        # TODO: Implement metrics collection
        return {
            "total_escalations": 0,
            "escalations_by_level": {},
            "escalations_by_reason": {},
            "average_resolution_time": 0
        } 