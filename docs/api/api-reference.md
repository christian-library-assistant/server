# Christian Library Assistant - API Reference

A comprehensive API reference for the Christian Library Assistant, a sophisticated RAG-powered API server for theological research and Christian text analysis.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**Content-Type:** `application/json`

## 📋 Table of Contents

- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Data Models](#data-models)
- [Endpoints](#endpoints)
  - [Testing Endpoints](#testing-endpoints)
  - [Query Endpoints](#query-endpoints)
  - [Session Management](#session-management)
  - [Utility Endpoints](#utility-endpoints)

## 🔐 Authentication

Currently, no authentication is required for any endpoints. All endpoints are publicly accessible.

## ❌ Error Handling

All endpoints return consistent error responses:

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

### Common Error Examples
```json
// Missing required field
{
  "detail": "Field 'query' is required"
}

// Session not found
{
  "detail": "Session not found"
}

// Configuration error
{
  "detail": "MANTICORE_API_URL not configured"
}
```

## 📊 Data Models

### UserQuery
Used for standard query requests.

```json
{
  "query": "string",                              // Required: The question or search text
  "top_k": 5,                                    // Optional: Number of results (default: 5)
  "conversation_history": [                       // Optional: Previous conversation
    {
      "role": "user|assistant",
      "content": "string"
    }
  ],
  "session_id": "string"                         // Optional: Session identifier
}
```

### AssistantResponse
Standard response format for query endpoints.

```json
{
  "answer": "string",                            // AI-generated response
  "sources": [                                   // Optional: Source citations
    {
      "record_id": "string",
      "link": "string", 
      "citation_text": "string"
    }
  ],
  "conversation_history": [                      // Optional: Updated conversation
    {
      "role": "user|assistant",
      "content": "string"
    }
  ],
  "session_id": "string"                        // Optional: Session identifier
}
```

### TestQueryRequest
Used for testing endpoint requests.

```json
{
  "query": "string",                            // Required: The question or search text
  "agentic": false,                            // Optional: Use agentic RAG (default: false)
  "top_k": 5,                                  // Optional: Number of results (default: 5)
  "return_fields": ["record_id"]               // Optional: Fields to return (default: ["record_id"])
}
```

### TestResponse
Response format for testing endpoint.

```json
{
  "query": "string",                           // Echo of original query
  "agentic_mode": false,                       // Which mode was used
  "results": [                                 // Array of search results
    {
      "field_name": "value"                    // Dynamic based on return_fields
    }
  ],
  "ai_answer": "string",                       // AI-generated response (nullable)
  "processing_info": {                         // Processing metadata
    "mode": "regular|agentic",
    "top_k": 5,
    "requested_fields": ["string"],
    "processing_time_seconds": 1.234,
    "results_returned": 5,
    "sources_found": 8,
    "session_cleaned": true,                   // Agentic mode only
    "agent_error": "string",                   // Present if error occurred
    "rag_error": "string",                     // Present if error occurred
    "fallback_to_search": false                // Whether fallback was used
  }
}
```

## 🔗 Endpoints

## Testing Endpoints

### POST /test
🧪 **Compare RAG Systems** - Test and compare Agentic vs Regular RAG without session state.

#### Request Body
```json
{
  "query": "What is salvation?",               // Required
  "agentic": false,                           // Optional (default: false)
  "top_k": 5,                                 // Optional (default: 5)
  "return_fields": ["record_id", "text"]      // Optional (default: ["record_id"])
}
```

#### Response
```json
{
  "query": "What is salvation?",
  "agentic_mode": false,
  "results": [
    {
      "record_id": "augustine.confessions.viii.12",
      "text": "For salvation is the deliverance from sin..."
    }
  ],
  "ai_answer": "Salvation is the deliverance from sin and its consequences...",
  "processing_info": {
    "mode": "regular",
    "top_k": 5,
    "requested_fields": ["record_id", "text"],
    "processing_time_seconds": 1.234,
    "results_returned": 1,
    "sources_found": 5
  }
}
```

#### Available Return Fields
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Unique identifier for each result |
| `text` | string | The actual content/paragraph text |
| `authorid` | string | Author identifier |
| `workid` | string | Work/book identifier |
| `versionid` | string | Version identifier |
| `sectionid` | string | Section identifier |
| `docid` | integer | Document ID |
| `knn_distance` | float | Semantic similarity score |
| `refs` | array | References/citations |
| `link` | string | URL link to source |
| `citation_text` | string | Formatted citation |
| `answer` | string | AI-generated response |

#### Example Requests

**Basic Request:**
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is prayer?"
  }'
```

**Advanced Request:**
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How did Augustine view divine grace?",
    "agentic": true,
    "top_k": 10,
    "return_fields": ["record_id", "text", "authorid", "workid", "answer", "citation_text"]
  }'
```

### GET /test/fields
📋 **Get Available Fields** - Returns all fields that can be requested in the test endpoint.

#### Request
No request body required.

#### Response
```json
{
  "available_fields": [
    "record_id",
    "text",
    "authorid",
    "workid",
    "versionid",
    "sectionid", 
    "docid",
    "knn_distance",
    "refs",
    "link",
    "citation_text",
    "answer"
  ],
  "field_descriptions": {
    "record_id": "Unique identifier for each result",
    "text": "The actual content/paragraph text",
    "authorid": "Author identifier",
    "workid": "Work/book identifier",
    "versionid": "Version identifier",
    "sectionid": "Section identifier",
    "docid": "Document ID",
    "knn_distance": "Semantic similarity score",
    "refs": "References/citations",
    "link": "URL link to source",
    "citation_text": "Formatted citation",
    "answer": "AI-generated response"
  },
  "usage_example": {
    "query": "What is the nature of God?",
    "agentic": true,
    "top_k": 5,
    "return_fields": ["record_id", "text", "authorid", "workid", "answer"]
  }
}
```

#### Example Request
```bash
curl -X GET "http://localhost:8000/test/fields"
```

## Query Endpoints

### POST /query
💬 **Regular RAG Query** - Process queries using the standard RAG system.

#### Request Body
```json
{
  "query": "What did Augustine teach about grace?",  // Required
  "top_k": 5,                                      // Optional (default: 5)
  "conversation_history": [                         // Optional
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant", 
      "content": "Previous answer"
    }
  ],
  "session_id": "optional-session-id"              // Optional
}
```

#### Response
```json
{
  "answer": "Augustine taught that divine grace is absolutely necessary for salvation...",
  "sources": [
    {
      "record_id": "augustine.grace.freewill.i.5",
      "link": "https://ccel.org/ccel/augustine.grace.freewill.i.5",
      "citation_text": "Augustine, On Grace and Free Will, Book I, Chapter 5"
    }
  ],
  "conversation_history": [
    {
      "role": "user",
      "content": "What did Augustine teach about grace?"
    },
    {
      "role": "assistant",
      "content": "Augustine taught that divine grace is absolutely necessary..."
    }
  ],
  "session_id": null
}
```

#### Example Request
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the relationship between faith and reason?",
    "top_k": 3
  }'
```

### POST /query-agent
🤖 **Agentic RAG Query** - Process queries using the advanced agentic RAG system with reasoning capabilities.

#### Session ID Management
**IMPORTANT**: Session IDs are **NOT automatic**. You must manage them manually for conversation continuity.

**Two ways to pass session ID:**
1. **Header (Recommended)**: `X-Session-ID: your-session-id`
2. **Request Body**: `"session_id": "your-session-id"`

**Priority**: Header takes precedence over request body field.

**Session ID Guidelines:**
- Use any unique string (UUIDs recommended)
- Same session ID = conversation continues with memory
- Different/no session ID = new conversation starts
- Sessions persist until explicitly deleted

#### Headers
- `X-Session-ID` (optional): Session identifier for conversation continuity

#### Request Body
```json
{
  "query": "How do different Church Fathers view the Trinity?",  // Required
  "top_k": 5,                                                  // Optional (default: 5)
  "conversation_history": [                                     // Optional
    {
      "role": "user",
      "content": "Previous question"
    }
  ],
  "session_id": "session-123"                                  // Optional (can use header instead)
}
```

#### Response
```json
{
  "answer": "The Church Fathers approached the Trinity with varying emphases...",
  "sources": [
    {
      "record_id": "athanasius.against.arians.i.15",
      "link": "https://ccel.org/ccel/athanasius.against.arians.i.15",
      "citation_text": "Athanasius, Against the Arians, Book I, Chapter 15"
    },
    {
      "record_id": "basil.holy.spirit.ix.22",
      "link": "https://ccel.org/ccel/basil.holy.spirit.ix.22", 
      "citation_text": "Basil, On the Holy Spirit, Chapter IX, Section 22"
    }
  ],
  "conversation_history": [
    {
      "role": "user",
      "content": "How do different Church Fathers view the Trinity?"
    },
    {
      "role": "assistant",
      "content": "The Church Fathers approached the Trinity with varying emphases..."
    }
  ],
  "session_id": "session-123"
}
```

#### Example Request
```bash
curl -X POST "http://localhost:8000/query-agent" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: my-session-123" \
  -d '{
    "query": "What are the arguments for and against infant baptism?",
    "top_k": 8
  }'
```

## Session Management

### POST /query-agent-reset
🔄 **Reset Session** - Reset a specific session's conversation memory.

#### Headers
- `X-Session-ID` (required): Session identifier to reset

#### Request Body
No request body required.

#### Response
```json
{
  "message": "Agent conversation reset successfully",
  "session_id": "session-123"
}
```

#### Error Responses
```json
// Session ID missing
{
  "detail": "Session ID is required in X-Session-ID header"
}

// Session not found
{
  "detail": "Session not found"
}
```

#### Example Request
```bash
curl -X POST "http://localhost:8000/query-agent-reset" \
  -H "X-Session-ID: session-123"
```

### DELETE /query-agent-session
🗑️ **Delete Session** - Delete a specific session entirely.

#### Headers
- `X-Session-ID` (required): Session identifier to delete

#### Request Body
No request body required.

#### Response
```json
{
  "message": "Session deleted successfully",
  "session_id": "session-123"
}
```

#### Error Responses
```json
// Session ID missing
{
  "detail": "Session ID is required in X-Session-ID header"
}

// Session not found
{
  "detail": "Session not found"
}
```

#### Example Request
```bash
curl -X DELETE "http://localhost:8000/query-agent-session" \
  -H "X-Session-ID: session-123"
```

### GET /query-agent-sessions
📊 **Get Session Info** - Get information about sessions.

#### Headers
- `X-Session-ID` (optional): Specific session ID to get info for

#### Request Body
No request body required.

#### Response

**With Session ID (specific session info):**
```json
{
  "session_id": "session-123",
  "created_at": "2025-09-23T10:30:00Z",
  "last_activity": "2025-09-23T11:45:00Z",
  "message_count": 5,
  "status": "active"
}
```

**Without Session ID (all sessions):**
```json
{
  "total_sessions": 3,
  "active_sessions": 2,
  "sessions": [
    {
      "session_id": "session-123",
      "created_at": "2025-09-23T10:30:00Z",
      "last_activity": "2025-09-23T11:45:00Z",
      "message_count": 5,
      "status": "active"
    },
    {
      "session_id": "session-456",
      "created_at": "2025-09-23T09:15:00Z",
      "last_activity": "2025-09-23T09:30:00Z",
      "message_count": 2,
      "status": "inactive"
    }
  ]
}
```

#### Example Requests
```bash
# Get specific session info
curl -X GET "http://localhost:8000/query-agent-sessions" \
  -H "X-Session-ID: session-123"

# Get all sessions info
curl -X GET "http://localhost:8000/query-agent-sessions"
```

## Utility Endpoints

### GET /record-ids
🔍 **Get Record IDs** - Get record IDs from text query using direct Manticore search.

#### Query Parameters
- `query` (required): The search text

#### Request
No request body required. Uses query parameters.

#### Response
```json
[
  "augustine.confessions.viii.12",
  "aquinas.summa.ii-ii.q2.a1",
  "chrysostom.homilies.matthew.lv.3"
]
```

#### Example Request
```bash
curl -X GET "http://localhost:8000/record-ids?query=salvation"
```

## 🚀 Usage Examples

### Research Workflow Example

```bash
# 1. Get available fields for testing
curl -X GET "http://localhost:8000/test/fields"

# 2. Test both RAG approaches for comparison
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the relationship between faith and works in salvation?",
    "agentic": false,
    "return_fields": ["record_id", "text", "authorid", "answer"]
  }' > regular_results.json

curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the relationship between faith and works in salvation?", 
    "agentic": true,
    "return_fields": ["record_id", "text", "authorid", "answer"]
  }' > agentic_results.json

# 3. Start a persistent research session
curl -X POST "http://localhost:8000/query-agent" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: research-session-001" \
  -d '{
    "query": "What did Augustine teach about predestination?",
    "top_k": 5
  }'

# 4. Continue the conversation
curl -X POST "http://localhost:8000/query-agent" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: research-session-001" \
  -d '{
    "query": "How does this compare to Calvin perspective?",
    "top_k": 5
  }'

# 5. Get session information
curl -X GET "http://localhost:8000/query-agent-sessions" \
  -H "X-Session-ID: research-session-001"

# 6. Clean up session when done
curl -X DELETE "http://localhost:8000/query-agent-session" \
  -H "X-Session-ID: research-session-001"
```

### Batch Processing Example

```bash
#!/bin/bash
# Process multiple theological questions

queries=(
  "What is the nature of God?"
  "How is salvation obtained?"
  "What is the role of scripture?"
  "What is the purpose of prayer?"
)

for query in "${queries[@]}"; do
  echo "Processing: $query"
  curl -s -X POST "http://localhost:8000/test" \
    -H "Content-Type: application/json" \
    -d "{
      \"query\": \"$query\",
      \"agentic\": true,
      \"return_fields\": [\"record_id\", \"answer\", \"authorid\"]
    }" | jq -r '.ai_answer' > "answer_$(echo "$query" | tr ' ?' '_').txt"
done
```

## 📊 Performance Guidelines

### Response Times (Typical)
- **GET /test/fields**: < 100ms
- **GET /record-ids**: 200-500ms  
- **POST /test** (Regular): 1-3 seconds
- **POST /test** (Agentic): 2-5 seconds
- **POST /query**: 1-3 seconds
- **POST /query-agent**: 2-6 seconds
- **Session operations**: < 200ms

### Optimization Tips
- Use `top_k=3` for faster responses
- Request minimal `return_fields` for testing
- Use Regular RAG for simple queries
- Use Agentic RAG for complex reasoning
- Reuse sessions for conversation continuity

## � Session Management Best Practices

### Session ID Strategy
```bash
# Good: Use UUIDs for uniqueness
SESSION_ID="550e8400-e29b-41d4-a716-446655440000"

# Good: Use descriptive prefixes
SESSION_ID="research-trinity-$(date +%s)"

# Good: Use user-specific identifiers
SESSION_ID="user-123-conversation-456"
```

### Conversation Flow Best Practices

#### 1. Start a Research Session
```bash
# Create a unique session for your research topic
curl -X POST "http://localhost:8000/query-agent" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: research-predestination-001" \
  -d '{"query": "What did Augustine teach about predestination?"}'
```

#### 2. Build Context Through Follow-ups
```bash
# Ask follow-up questions in the same session
curl -X POST "http://localhost:8000/query-agent" \
  -H "X-Session-ID: research-predestination-001" \
  -d '{"query": "How did later theologians respond to this?"}'

curl -X POST "http://localhost:8000/query-agent" \
  -H "X-Session-ID: research-predestination-001" \
  -d '{"query": "What are the main objections to this view?"}'
```

#### 3. Monitor Session Health
```bash
# Check how many messages are in your session
curl -X GET "http://localhost:8000/query-agent-sessions" \
  -H "X-Session-ID: research-predestination-001"
```

#### 4. Reset When Changing Topics
```bash
# Reset conversation memory while keeping session alive
curl -X POST "http://localhost:8000/query-agent-reset" \
  -H "X-Session-ID: research-predestination-001"

# Now start a new topic in the same session
curl -X POST "http://localhost:8000/query-agent" \
  -H "X-Session-ID: research-predestination-001" \
  -d '{"query": "What is the role of free will in salvation?"}'
```

#### 5. Clean Up When Done
```bash
# Delete session to free resources
curl -X DELETE "http://localhost:8000/query-agent-session" \
  -H "X-Session-ID: research-predestination-001"
```

### Session Management Patterns

#### Pattern 1: Single Research Topic
```bash
SESSION_ID="topic-$(date +%s)"
# Use for focused research on one subject
# Delete when topic research is complete
```

#### Pattern 2: User-Based Sessions
```bash
SESSION_ID="user-$USER_ID-$(date +%Y%m%d)"
# One session per user per day
# Reset daily for fresh conversations
```

#### Pattern 3: Multi-Topic Research
```bash
SESSION_ID="comparative-study-trinity-incarnation"
# Use resets to separate topics within same session
# Allows building complex comparative analysis
```

### Common Session Pitfalls

❌ **Don't**: Use the same session ID across different users  
✅ **Do**: Create unique sessions for each user/context

❌ **Don't**: Let sessions grow indefinitely  
✅ **Do**: Reset or delete sessions periodically

❌ **Don't**: Forget to clean up test sessions  
✅ **Do**: Delete sessions when research is complete

❌ **Don't**: Use predictable session IDs in production  
✅ **Do**: Use UUIDs or cryptographically secure identifiers

## �🔧 Rate Limiting

Currently, no rate limiting is implemented. For production use, consider:
- Implementing client-side throttling
- Using connection pooling
- Caching frequent queries
- Monitoring resource usage

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- Session IDs can be any string (recommend UUIDs)
- Conversation history is maintained automatically in agentic mode
- Fallback mechanisms ensure responses even when AI services fail
- All endpoints support CORS for browser-based applications

---

*For more examples and detailed guides, see the [Testing Endpoint Documentation](testing-endpoint.md) and [Practical Examples](testing-endpoint-examples.md).*