import logging
from typing import Dict, Any, List, Optional
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMemory

logger = logging.getLogger(__name__)


class TicketMemory(BaseMemory):
    """
    Custom Langchain memory subclass for managing conversation history per ticket and email.
    """
    
    # TODO: Replace with a persistent database (e.g., PostgreSQL, Redis)
    # This is an in-memory store for demonstration purposes.
    store: Dict[str, List[Dict[str, Any]]] = {}
    
    @property
    def memory_variables(self) -> List[str]:
        """
        The string keys this memory uses to pull information from the chain.
        """
        return ["conversation_history"]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables from the store.
        """
        ticket_id = inputs.get("ticket_id")
        email_id = inputs.get("email_id")
        
        if ticket_id:
            history = self.store.get(ticket_id, [])
            logger.debug(f"Loaded memory for ticket {ticket_id}: {len(history)} entries")
            return {"conversation_history": history}
        elif email_id:
            # TODO: Implement logic to retrieve history based on email_id if needed
            logger.warning(f"Loading memory by email_id ({email_id}) is not fully implemented.")
            return {"conversation_history": []}
        
        logger.warning("No ticket_id or email_id provided for memory loading.")
        return {"conversation_history": []}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """
        Save context from this interaction to buffer.
        """
        ticket_id = inputs.get("ticket_id")
        email_id = inputs.get("email_id")
        
        if not ticket_id and not email_id:
            logger.warning("Cannot save context: No ticket_id or email_id provided.")
            return
        
        # Construct message entry
        message_entry = {
            "timestamp": inputs.get("timestamp"),
            "sender": inputs.get("sender"),
            "email_body": inputs.get("email_body"),
            "intent": outputs.get("intent"),
            "entities": outputs.get("entities"),
            "response_body": outputs.get("response_body"),
            "response_attachments": outputs.get("response_attachments"),
        }
        
        if ticket_id:
            if ticket_id not in self.store:
                self.store[ticket_id] = []
            self.store[ticket_id].append(message_entry)
            logger.debug(f"Saved context for ticket {ticket_id}. Total entries: {len(self.store[ticket_id])}")
        
        # TODO: If email_id is used as key, ensure it's handled consistently
        # For now, assuming ticket_id is the primary key for conversation history
    
    def clear(self):
        """
        Clear memory contents.
        """
        self.store = {}
        logger.info("Cleared all memory stores.")
    
    def get_conversation_history(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the full conversation history for a given ticket ID.
        """
        return self.store.get(ticket_id, [])
    
    def update_conversation(
        self,
        ticket_id: str,
        parsed_email: Dict[str, Any],
        intent_result: Dict[str, Any],
        response: Optional[Dict[str, Any]] = None
    ):
        """
        Update conversation history with incoming email and outgoing response.
        """
        if ticket_id not in self.store:
            self.store[ticket_id] = []
        
        # Add incoming email
        self.store[ticket_id].append({
            "type": "incoming",
            "timestamp": parsed_email.get("date"),
            "sender": parsed_email.get("sender"),
            "subject": parsed_email.get("subject"),
            "body": parsed_email.get("body"),
            "email_id": parsed_email.get("id"),
            "intent": intent_result.get("intent"),
            "entities": intent_result.get("entities"),
        })
        
        # Add outgoing response if available
        if response:
            self.store[ticket_id].append({
                "type": "outgoing",
                "timestamp": str(datetime.now()), # TODO: Use actual response time
                "recipient": parsed_email.get("sender"),
                "subject": f"Re: {parsed_email.get("subject")}",
                "body": response.get("body"),
                "attachments": response.get("attachments"),
            })
        
        logger.debug(f"Updated conversation for ticket {ticket_id}. Current length: {len(self.store[ticket_id])}")


# TODO: Integrate with a persistent database (e.g., SQLAlchemy) for production use.
# Example of how to integrate with SQLAlchemy (conceptual):
# from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from datetime import datetime

# Base = declarative_base()

# class ConversationEntry(Base):
#     __tablename__ = "conversation_history"
#     id = Column(Integer, primary_key=True)
#     ticket_id = Column(String, index=True)
#     email_id = Column(String, index=True, nullable=True)
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     entry_type = Column(String) # 'incoming' or 'outgoing'
#     sender = Column(String, nullable=True)
#     recipient = Column(String, nullable=True)
#     subject = Column(String, nullable=True)
#     body = Column(Text)
#     intent = Column(String, nullable=True)
#     entities = Column(Text, nullable=True) # Store as JSON string
#     attachments = Column(Text, nullable=True) # Store as JSON string

# class PersistentTicketMemory(TicketMemory):
#     def __init__(self, db_url: str):
#         super().__init__()
#         self.engine = create_engine(db_url)
#         Base.metadata.create_all(self.engine)
#         self.Session = sessionmaker(bind=self.engine)

#     def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         ticket_id = inputs.get("ticket_id")
#         if not ticket_id: return {"conversation_history": []}

#         session = self.Session()
#         entries = session.query(ConversationEntry).filter_by(ticket_id=ticket_id).order_by(ConversationEntry.timestamp).all()
#         session.close()

#         history = []
#         for entry in entries:
#             history.append({
#                 "type": entry.entry_type,
#                 "timestamp": str(entry.timestamp),
#                 "sender": entry.sender,
#                 "recipient": entry.recipient,
#                 "subject": entry.subject,
#                 "body": entry.body,
#                 "email_id": entry.email_id,
#                 "intent": entry.intent,
#                 "entities": json.loads(entry.entities) if entry.entities else {},
#                 "attachments": json.loads(entry.attachments) if entry.attachments else [],
#             })
#         return {"conversation_history": history}

#     def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
#         ticket_id = inputs.get("ticket_id")
#         if not ticket_id: return

#         session = self.Session()
#         # Save incoming email
#         incoming_entry = ConversationEntry(
#             ticket_id=ticket_id,
#             email_id=inputs.get("email_id"),
#             entry_type="incoming",
#             sender=inputs.get("sender"),
#             subject=inputs.get("subject"),
#             body=inputs.get("email_body"),
#             intent=outputs.get("intent"),
#             entities=json.dumps(outputs.get("entities", {})),
#         )
#         session.add(incoming_entry)

#         # Save outgoing response
#         if outputs.get("response_body"):
#             outgoing_entry = ConversationEntry(
#                 ticket_id=ticket_id,
#                 entry_type="outgoing",
#                 recipient=inputs.get("sender"), # Assuming reply to sender
#                 subject=outputs.get("response_subject"),
#                 body=outputs.get("response_body"),
#                 attachments=json.dumps(outputs.get("response_attachments", [])),
#             )
#             session.add(outgoing_entry)

#         session.commit()
#         session.close()

#     def clear(self):
#         session = self.Session()
#         session.query(ConversationEntry).delete()
#         session.commit()
#         session.close()

#     def get_conversation_history(self, ticket_id: str) -> List[Dict[str, Any]]:
#         session = self.Session()
#         entries = session.query(ConversationEntry).filter_by(ticket_id=ticket_id).order_by(ConversationEntry.timestamp).all()
#         session.close()
#         history = []
#         for entry in entries:
#             history.append({
#                 "type": entry.entry_type,
#                 "timestamp": str(entry.timestamp),
#                 "sender": entry.sender,
#                 "recipient": entry.recipient,
#                 "subject": entry.subject,
#                 "body": entry.body,
#                 "email_id": entry.email_id,
#                 "intent": entry.intent,
#                 "entities": json.loads(entry.entities) if entry.entities else {},
#                 "attachments": json.loads(entry.attachments) if entry.attachments else [],
#             })
#         return history


