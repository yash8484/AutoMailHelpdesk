# AutoMailHelpdesk API Specification

## Overview
This document describes the REST API endpoints provided by AutoMailHelpdesk for webhook handling, health checks, and manual operations.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://automailhelpdesk.yourdomain.com`

## Authentication
Most endpoints require authentication. The system uses JWT tokens for API access.

### Authentication Header
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Health Check Endpoints

#### GET /healthz
Returns the health status of the application.

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy

#### GET /readyz
Returns the readiness status of the application, including external dependencies.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "gmail_api": "ok",
    "odoo_api": "ok",
    "chromadb": "ok"
  }
}
```

**Status Codes:**
- `200 OK`: Service is ready
- `503 Service Unavailable`: Service is not ready

### Webhook Endpoints

#### POST /webhooks/gmail
Handles Gmail push notifications for new emails.

**Request Body:**
```json
{
  "message": {
    "data": "base64_encoded_message_data",
    "messageId": "gmail_message_id",
    "publishTime": "2023-01-01T00:00:00.000Z"
  },
  "subscription": "projects/project-id/subscriptions/subscription-name"
}
```

**Response:**
```json
{
  "status": "accepted",
  "message_id": "gmail_message_id"
}
```

**Status Codes:**
- `200 OK`: Webhook processed successfully
- `400 Bad Request`: Invalid payload
- `500 Internal Server Error`: Processing failed

#### POST /webhooks/manual-trigger
Manually triggers email processing (for testing/debugging).

**Request Body:** None

**Response:**
```json
{
  "status": "triggered"
}
```

**Status Codes:**
- `200 OK`: Manual trigger successful
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Trigger failed

### Ticket Management Endpoints

#### GET /tickets/{ticket_id}
Retrieves ticket information.

**Parameters:**
- `ticket_id` (path): Odoo ticket ID

**Response:**
```json
{
  "id": "12345",
  "subject": "Email subject",
  "status": "open",
  "priority": "medium",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z",
  "conversation_history": [
    {
      "type": "incoming",
      "timestamp": "2023-01-01T00:00:00Z",
      "sender": "customer@example.com",
      "body": "Email content",
      "intent": "general_query"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Ticket found
- `404 Not Found`: Ticket not found
- `401 Unauthorized`: Authentication required

#### PUT /tickets/{ticket_id}/status
Updates ticket status.

**Parameters:**
- `ticket_id` (path): Odoo ticket ID

**Request Body:**
```json
{
  "status": "closed",
  "resolution": "Issue resolved"
}
```

**Response:**
```json
{
  "id": "12345",
  "status": "closed",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Status updated
- `404 Not Found`: Ticket not found
- `401 Unauthorized`: Authentication required

### Knowledge Base Endpoints

#### POST /knowledge/documents
Adds documents to the knowledge base.

**Request Body:**
```json
{
  "documents": [
    {
      "content": "Document content",
      "metadata": {
        "source": "manual_upload",
        "category": "faq",
        "title": "Document title"
      }
    }
  ]
}
```

**Response:**
```json
{
  "added_count": 1,
  "document_ids": ["doc_123"]
}
```

**Status Codes:**
- `201 Created`: Documents added
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required

#### GET /knowledge/search
Searches the knowledge base.

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Maximum results (default: 5)

**Response:**
```json
{
  "results": [
    {
      "content": "Relevant document content",
      "metadata": {
        "source": "faq.pdf",
        "title": "Frequently Asked Questions"
      },
      "score": 0.85
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Search completed
- `400 Bad Request`: Invalid query
- `401 Unauthorized`: Authentication required

### Analytics Endpoints

#### GET /analytics/tickets
Returns ticket analytics.

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `intent` (optional): Filter by intent

**Response:**
```json
{
  "total_tickets": 150,
  "by_intent": {
    "general_query": 75,
    "bank_statement": 30,
    "password_update": 25,
    "urgent_human": 15,
    "fallback_human": 5
  },
  "by_status": {
    "open": 20,
    "in_progress": 10,
    "closed": 120
  },
  "average_resolution_time": "2.5 hours"
}
```

**Status Codes:**
- `200 OK`: Analytics retrieved
- `401 Unauthorized`: Authentication required

#### GET /analytics/performance
Returns system performance metrics.

**Response:**
```json
{
  "email_processing": {
    "total_processed": 1000,
    "average_processing_time": "30 seconds",
    "success_rate": 0.95
  },
  "intent_classification": {
    "accuracy": 0.92,
    "confidence_distribution": {
      "high": 0.70,
      "medium": 0.25,
      "low": 0.05
    }
  },
  "api_health": {
    "gmail_api": "healthy",
    "odoo_api": "healthy",
    "gemini_api": "healthy"
  }
}
```

**Status Codes:**
- `200 OK`: Metrics retrieved
- `401 Unauthorized`: Authentication required

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "bad_request",
  "message": "Invalid request format",
  "details": {
    "field": "email",
    "issue": "required field missing"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "request_id": "req_123456"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- **Default**: 100 requests per minute per IP
- **Webhook endpoints**: 1000 requests per minute
- **Analytics endpoints**: 10 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhook Security

Gmail webhooks should be validated using the following methods:
1. **Signature Verification**: Verify the webhook signature using your webhook secret
2. **IP Allowlisting**: Only accept webhooks from Google's IP ranges
3. **HTTPS Only**: All webhook endpoints must use HTTPS in production

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- **Development**: `http://localhost:8000/docs`
- **Production**: `https://automailhelpdesk.yourdomain.com/docs`

Interactive API documentation (Swagger UI) is available at:
- **Development**: `http://localhost:8000/docs`
- **Production**: `https://automailhelpdesk.yourdomain.com/docs`

Alternative documentation (ReDoc) is available at:
- **Development**: `http://localhost:8000/redoc`
- **Production**: `https://automailhelpdesk.yourdomain.com/redoc`

