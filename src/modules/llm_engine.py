import logging
from typing import Dict, Any, Optional, List
from langchain.llms import GooglePalm
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMemory
from langsmith import Client
from tenacity import retry, stop_after_attempt, wait_exponential
from ..settings import settings

logger = logging.getLogger(__name__)


class LLMEngine:
    """
    LLM engine using Gemini via Langchain for intent classification and response generation.
    """
    
    def __init__(self):
        # Initialize Gemini LLM
        self.llm = GooglePalm(
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            max_output_tokens=1024
        )
        
        # Initialize Langsmith client for tracing
        self.langsmith_client = Client(
            api_url=settings.LANGCHAIN_ENDPOINT,
            api_key=settings.LANGCHAIN_API_KEY
        )
        
        # Initialize prompt templates
        self._setup_prompts()
    
    def _setup_prompts(self):
        """
        Setup prompt templates for different tasks.
        """
        # Intent classification prompt
        self.intent_classification_prompt = PromptTemplate(
            input_variables=["email_body", "sender", "conversation_history"],
            template="""
You are an AI assistant that classifies customer support emails into specific intents.

Email from: {sender}
Email content: {email_body}

Previous conversation (if any): {conversation_history}

Classify this email into one of these intents:
1. bank_statement - Customer requesting bank statements
2. password_update - Customer wanting to update their password
3. general_query - General questions about products/services
4. urgent_human - Urgent issues requiring immediate human attention
5. fallback_human - Complex issues that need human review

For each intent, also extract relevant entities:
- bank_statement: months (number of months requested)
- password_update: current_pw, new_pw (if provided)
- general_query: topic, specific_question
- urgent_human: urgency_level, issue_type
- fallback_human: complexity_reason

Respond in JSON format:
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "entities": {{
        "key": "value"
    }},
    "reasoning": "Brief explanation of classification"
}}
"""
        )
        
        # RAG response generation prompt
        self.rag_response_prompt = PromptTemplate(
            input_variables=["question", "context", "conversation_history"],
            template="""
You are a helpful customer support assistant. Answer the customer's question based on the provided context and conversation history.

Customer question: {question}

Relevant context from knowledge base:
{context}

Previous conversation: {conversation_history}

Provide a helpful, accurate, and professional response. If you cannot answer based on the context, politely explain what information you need or suggest contacting human support.

Include citations for any specific information you reference from the context.

Response:
"""
        )
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def classify_intent(
        self,
        email_body: str,
        sender: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Classify email intent using Gemini LLM.
        """
        try:
            # Format conversation history
            history_text = ""
            if conversation_history:
                history_text = "\n".join([
                    f"- {msg.get('date', '')}: {msg.get('body', '')[:100]}..."
                    for msg in conversation_history[-5:]  # Last 5 messages
                ])
            
            # Create LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=self.intent_classification_prompt,
                verbose=True
            )
            
            # Run classification
            result = chain.run(
                email_body=email_body,
                sender=sender,
                conversation_history=history_text
            )
            
            # Parse JSON response
            import json
            try:
                parsed_result = json.loads(result.strip())
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning(f"Failed to parse LLM response as JSON: {result}")
                parsed_result = {
                    "intent": "fallback_human",
                    "confidence": 0.5,
                    "entities": {},
                    "reasoning": "Failed to parse LLM response"
                }
            
            # Log to Langsmith
            self._log_to_langsmith("intent_classification", {
                "input": {"email_body": email_body, "sender": sender},
                "output": parsed_result
            })
            
            logger.info(f"Classified intent: {parsed_result['intent']} (confidence: {parsed_result['confidence']})")
            return parsed_result
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Return fallback intent
            return {
                "intent": "fallback_human",
                "confidence": 0.0,
                "entities": {},
                "reasoning": f"Classification error: {str(e)}"
            }
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_rag_response(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate response using RAG (Retrieval-Augmented Generation).
        """
        try:
            # Format conversation history
            history_text = ""
            if conversation_history:
                history_text = "\n".join([
                    f"- {msg.get('date', '')}: {msg.get('body', '')[:200]}..."
                    for msg in conversation_history[-3:]  # Last 3 messages
                ])
            
            # Create LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=self.rag_response_prompt,
                verbose=True
            )
            
            # Generate response
            response = chain.run(
                question=question,
                context=context,
                conversation_history=history_text
            )
            
            # Log to Langsmith
            self._log_to_langsmith("rag_response", {
                "input": {"question": question, "context": context[:500]},
                "output": {"response": response}
            })
            
            logger.info(f"Generated RAG response for question: {question[:50]}...")
            return response.strip()
        
        except Exception as e:
            logger.error(f"RAG response generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please contact our human support team for assistance."
    
    def _log_to_langsmith(self, operation: str, data: Dict[str, Any]):
        """
        Log operation to Langsmith for monitoring and debugging.
        """
        try:
            # TODO: Implement proper Langsmith logging
            # This is a placeholder - implement based on Langsmith SDK
            logger.debug(f"Langsmith log - {operation}: {data}")
        except Exception as e:
            logger.warning(f"Failed to log to Langsmith: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for text using Google Embedding API.
        """
        try:
            # TODO: Implement Google Embedding API call
            # This is a placeholder - implement actual embedding generation
            from google.cloud import aiplatform
            
            # Initialize AI Platform client
            # client = aiplatform.gapic.PredictionServiceClient()
            
            # For now, return dummy embedding
            logger.warning("Using dummy embedding - implement actual Google Embedding API")
            return [0.0] * 768  # Dummy 768-dimensional embedding
        
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * 768  # Return zero embedding as fallback
    
    # TODO: Add more methods for different LLM tasks (summarization, translation, etc.)

