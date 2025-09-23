# Testing Endpoint API Documentation

## Overview

The Testing Endpoint (`/test`) is a powerful experimental tool designed to compare and evaluate the performance of two different RAG (Retrieval-Augmented Generation) systems:

- **Regular RAG**: Traditional retrieval-augmented generation
- **Agentic RAG**: Advanced agentic system with reasoning capabilities

This endpoint operates **without session state**, making it perfect for experimentation, benchmarking, and one-off queries.

## Endpoints

### 1. `/test` - Main Testing Endpoint

**Method:** `POST`  
**Content-Type:** `application/json`

#### Request Schema

```json
{
  "query": "string",           // Required: Your question or search text
  "agentic": boolean,          // Optional: true for Agentic RAG, false for Regular RAG (default: false)
  "top_k": integer,           // Optional: Number of results to retrieve (default: 5)
  "return_fields": ["string"] // Optional: Fields to include in response (default: ["record_id"])
}
```

#### Response Schema

```json
{
  "query": "string",                    // Echo of your original query
  "agentic_mode": boolean,              // Which mode was used
  "results": [                          // Array of search results
    {
      "field_name": "value",            // Dynamic based on return_fields
      "another_field": "another_value"
    }
  ],
  "ai_answer": "string",               // AI-generated response (nullable)
  "processing_info": {                 // Metadata about the processing
    "mode": "string",                  // "agentic" or "regular"
    "top_k": integer,                  // Number of results requested
    "requested_fields": ["string"],    // Fields that were requested
    "processing_time_seconds": float,  // How long it took to process
    "results_returned": integer,       // Actual number of results returned
    "sources_found": integer,          // Number of sources found by RAG system
    "session_cleaned": boolean,        // Whether agentic session was cleaned up (agentic mode only)
    // Error fields (only present if errors occurred)
    "agent_error": "string",           // Error message if agentic processing failed
    "rag_error": "string",             // Error message if regular RAG failed
    "fallback_to_search": boolean      // Whether system fell back to basic search
  }
}
```

### 2. `/test/fields` - Available Fields Reference

**Method:** `GET`

Returns information about all available fields that can be requested in the `return_fields` parameter.

#### Response Schema

```json
{
  "available_fields": ["string"],      // List of all available field names
  "field_descriptions": {              // Descriptions of what each field contains
    "field_name": "description"
  },
  "usage_example": {                   // Example of how to use the endpoint
    "query": "string",
    "agentic": boolean,
    "top_k": integer,
    "return_fields": ["string"]
  }
}
```

## Available Return Fields

The `return_fields` parameter allows you to customize exactly what data you want back. Here are all available fields:

| Field Name | Type | Description |
|------------|------|-------------|
| `record_id` | string | Unique identifier for each result |
| `text` | string | The actual content/paragraph text from the source |
| `authorid` | string | Author identifier |
| `workid` | string | Work/book identifier |
| `versionid` | string | Version identifier |
| `sectionid` | string | Section identifier |
| `docid` | integer | Document ID |
| `knn_distance` | float | Semantic similarity score (lower = more similar) |
| `refs` | array | References/citations |
| `link` | string | Generated URL link to source |
| `citation_text` | string | Formatted citation text |
| `answer` | string | AI-generated response (same for all results in a query) |

## Request Examples

### Example 1: Basic Query with Default Settings

```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is salvation?"
  }'
```

**Response:**
```json
{
  "query": "What is salvation?",
  "agentic_mode": false,
  "results": [
    {
      "record_id": "augustine.confessions.viii.12"
    },
    {
      "record_id": "aquinas.summa.ii-ii.q2.a1"
    }
  ],
  "ai_answer": "Salvation is the deliverance from sin and its consequences...",
  "processing_info": {
    "mode": "regular",
    "top_k": 5,
    "requested_fields": ["record_id"],
    "processing_time_seconds": 1.234,
    "results_returned": 2,
    "sources_found": 5
  }
}
```

### Example 2: Agentic Mode with Custom Fields

```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the Trinity",
    "agentic": true,
    "top_k": 3,
    "return_fields": ["record_id", "text", "authorid", "workid", "answer"]
  }'
```

**Response:**
```json
{
  "query": "Explain the Trinity",
  "agentic_mode": true,
  "results": [
    {
      "record_id": "augustine.trinity.i.4",
      "text": "The Father is God, the Son is God, and the Holy Spirit is God...",
      "authorid": "augustine",
      "workid": "trinity",
      "answer": "The Trinity is the Christian doctrine that God exists as three persons..."
    },
    {
      "record_id": "aquinas.summa.i.q27.a1",
      "text": "In God there are relations which are really distinct from each other...",
      "authorid": "aquinas", 
      "workid": "summa",
      "answer": "The Trinity is the Christian doctrine that God exists as three persons..."
    }
  ],
  "ai_answer": "The Trinity is the Christian doctrine that God exists as three persons...",
  "processing_info": {
    "mode": "agentic",
    "top_k": 3,
    "requested_fields": ["record_id", "text", "authorid", "workid", "answer"],
    "processing_time_seconds": 2.567,
    "results_returned": 2,
    "sources_found": 8,
    "session_cleaned": true
  }
}
```

### Example 3: Full Data Extraction

```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is prayer?",
    "agentic": false,
    "top_k": 2,
    "return_fields": [
      "record_id", 
      "text", 
      "authorid", 
      "workid", 
      "knn_distance", 
      "link", 
      "citation_text"
    ]
  }'
```

### Example 4: Getting Available Fields

```bash
curl -X GET "http://localhost:8000/test/fields"
```

**Response:**
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
    // ... more descriptions
  },
  "usage_example": {
    "query": "What is the nature of God?",
    "agentic": true,
    "top_k": 5,
    "return_fields": ["record_id", "text", "authorid", "workid", "answer"]
  }
}
```

## Mode Comparison

### Regular RAG Mode (`"agentic": false`)

- **Speed**: Faster processing
- **Consistency**: Predictable response patterns
- **Use Case**: When you want straightforward retrieval and generation
- **Session**: No session management overhead

**Processing Flow:**
1. Query sent to search system (Manticore)
2. Retrieved documents sent to AI for response generation
3. Response formatted and returned

### Agentic RAG Mode (`"agentic": true`)

- **Intelligence**: Advanced reasoning and tool usage
- **Flexibility**: Can decide when and how to search
- **Quality**: Often provides more nuanced responses
- **Session**: Creates temporary session (automatically cleaned up)

**Processing Flow:**
1. Creates temporary session for agent
2. Agent analyzes query and decides search strategy
3. Agent may perform multiple searches or reasoning steps
4. AI generates response with full context
5. Session automatically deleted
6. Response formatted and returned

## Error Handling

The endpoint includes comprehensive error handling and fallback mechanisms:

### Common Error Scenarios

1. **Configuration Error**: Missing `MANTICORE_API_URL`
   ```json
   {
     "detail": "MANTICORE_API_URL not configured"
   }
   ```

2. **Invalid Request**: Malformed JSON or missing required fields
   ```json
   {
     "detail": "Validation error: query field is required"
   }
   ```

3. **Processing Error with Fallback**: When AI fails but search succeeds
   ```json
   {
     "processing_info": {
       "agent_error": "Agent processing failed: timeout",
       "fallback_to_search": true
     },
     "results": [
       {
         "record_id": "some.record",
         "answer": "Error: Could not generate AI response"
       }
     ]
   }
   ```

### Fallback Behavior

When the AI system fails, the endpoint automatically falls back to basic search results to ensure you always get some data back. This is indicated by:

- `"fallback_to_search": true` in `processing_info`
- Error messages in `agent_error` or `rag_error` fields
- AI answer fields will contain error messages

## Performance Considerations

### Timing

- **Regular RAG**: Typically 1-3 seconds
- **Agentic RAG**: Typically 2-5 seconds (due to reasoning overhead)
- Timing information is always included in `processing_info.processing_time_seconds`

### Rate Limiting

- No built-in rate limiting currently implemented
- Consider implementing client-side throttling for heavy usage

### Resource Usage

- Agentic mode uses more computational resources
- Each agentic request creates and destroys a temporary session
- Regular mode has lower memory footprint

## Best Practices

### 1. Field Selection Strategy

**For Performance Testing:**
```json
{
  "return_fields": ["record_id", "knn_distance"]
}
```

**For Content Analysis:**
```json
{
  "return_fields": ["record_id", "text", "authorid", "workid", "citation_text"]
}
```

**For AI Comparison:**
```json
{
  "return_fields": ["record_id", "text", "answer"]
}
```

### 2. Query Optimization

- **Specific queries** work better than vague ones
- **Theological terms** are well-understood by the system
- **Historical context** helps improve results

### 3. Mode Selection

**Use Regular RAG when:**
- You need fast responses
- You have straightforward questions
- You're doing bulk testing

**Use Agentic RAG when:**
- You have complex, multi-part questions
- You want the AI to reason about the query
- Quality is more important than speed

### 4. Monitoring and Debugging

Always check `processing_info` for:
- Performance metrics
- Error conditions
- Fallback indicators
- Source counts

## Integration Examples

### Python Client

```python
import requests
import json

def test_rag_query(query, agentic=False, fields=None):
    url = "http://localhost:8000/test"
    
    payload = {
        "query": query,
        "agentic": agentic,
        "return_fields": fields or ["record_id", "text", "answer"]
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
result = test_rag_query(
    "What did Augustine say about grace?", 
    agentic=True,
    fields=["record_id", "text", "authorid", "answer"]
)

print(f"Processing time: {result['processing_info']['processing_time_seconds']}")
print(f"AI Answer: {result['ai_answer']}")
```

### JavaScript Client

```javascript
async function testRagQuery(query, options = {}) {
    const response = await fetch('http://localhost:8000/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query,
            agentic: options.agentic || false,
            top_k: options.topK || 5,
            return_fields: options.returnFields || ['record_id']
        })
    });
    
    return await response.json();
}

// Example usage
const result = await testRagQuery("What is divine love?", {
    agentic: true,
    topK: 3,
    returnFields: ['record_id', 'text', 'authorid', 'answer']
});

console.log('Results:', result.results);
console.log('Processing time:', result.processing_info.processing_time_seconds);
```

## Troubleshooting

### Common Issues

1. **Empty Results**
   - Check if your query is too specific
   - Try broader theological terms
   - Verify `MANTICORE_API_URL` is accessible

2. **Slow Responses**
   - Reduce `top_k` value
   - Use fewer `return_fields`
   - Consider using Regular RAG mode

3. **AI Errors**
   - Check `processing_info` for error details
   - System will fallback to search results
   - Verify AI service configuration

4. **Field Not Found**
   - Use `/test/fields` to see available fields
   - Some fields may be empty for certain records
   - Unknown fields return error messages

### Debugging Tips

1. **Start Simple**: Begin with minimal request and add complexity
2. **Check Processing Info**: Always examine the `processing_info` object
3. **Compare Modes**: Test the same query in both modes
4. **Monitor Timing**: Use processing time to optimize requests

## Security Notes

- No authentication required for testing endpoint
- No session data is persisted
- Temporary agentic sessions are automatically cleaned up
- All queries are logged for debugging purposes

## API Versioning

Current version: `v1`  
The testing endpoint is considered experimental and may evolve based on usage patterns and feedback.

---

*For additional support or questions about the testing endpoint, please refer to the main API documentation or contact the development team.*