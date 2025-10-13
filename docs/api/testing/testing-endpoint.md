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
  "top_k": integer,            // Optional: Number of results to retrieve (default: 5)
  "return_fields": ["string"], // Optional: Fields to include in response (default: ["record_id"])
  "authors": ["string"],       // Optional: Filter results to specific author IDs (default: [])
  "works": ["string"]          // Optional: Filter results to specific work IDs (default: [])
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

## Filtering by Author or Work

Filters constrain searches to specific authors or works. When specified, the search system **only** returns results from those sources - this applies to both regular and agentic modes.

**Filter vs. Natural Language:**

| Approach | Example | Behavior |
|----------|---------|----------|
| **Filter (Enforced)** | `{"query": "What is grace?", "authors": ["augustine"]}` | System ONLY searches Augustine's works |
| **Natural Language** | `{"query": "What did Augustine say about grace?"}` | System searches all works, AI tries to focus on Augustine |

### Finding Author and Work IDs

Use discovery endpoints to find valid IDs:

```bash
# List all authors
GET /authors

# Search for specific author
GET /authors?query=augustine
# Returns: [{"author_id": "augustine", "similarity_score": 100}, ...]

# List all works
GET /works

# Search for specific work
GET /works?query=confessions
# Returns: [{"work_id": "confessions", "similarity_score": 100}, ...]
```

**Common IDs:** `augustine`, `aquinas`, `calvin`, `luther` (authors) • `confessions`, `city`, `summa`, `institutes` (works)

### Filter Examples

**Single author:**
```json
{"query": "What is grace?", "authors": ["augustine"]}
```

**Author + work:**
```json
{"query": "What is grace?", "authors": ["augustine"], "works": ["confessions"]}
```

**Multiple authors:**
```json
{"query": "Views on predestination", "authors": ["augustine", "calvin", "aquinas"]}
```

## Request Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is salvation?"}'
```

Response includes: `query`, `agentic_mode`, `results` array, `ai_answer`, `processing_info`

### With Filters
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is grace?",
    "agentic": true,
    "authors": ["augustine"],
    "return_fields": ["record_id", "text", "answer"]
  }'
```

### Get Available Fields
```bash
curl -X GET "http://localhost:8000/test/fields"
```

Returns list of all available `return_fields` with descriptions.

## Mode Comparison

| Feature | Regular (`agentic: false`) | Agentic (`agentic: true`) |
|---------|---------------------------|---------------------------|
| **Speed** | Faster (1-3s) | Slower (2-5s) |
| **Intelligence** | Basic retrieval + generation | Advanced reasoning & tool use |
| **Session** | Stateless | Temporary session (auto-cleanup) |
| **Use When** | Fast, straightforward queries | Complex, multi-part questions |

## Error Handling

The endpoint includes automatic fallback mechanisms:

- **Configuration errors**: Returns 503 with error detail
- **Invalid requests**: Returns 400 with validation error
- **AI failures**: Falls back to search results, sets `fallback_to_search: true` in `processing_info`
- Error details available in `agent_error` or `rag_error` fields

## Best Practices

**Field Selection:**
- Performance testing: `["record_id", "knn_distance"]`
- Content analysis: `["record_id", "text", "authorid", "workid"]`
- AI responses: `["record_id", "text", "answer"]`

**Query Optimization:**
- Use specific theological terms over vague language
- Add filters when researching specific authors/works
- Start broad, then filter if needed

**Mode Selection:**
- **Regular RAG**: Fast responses, straightforward queries, bulk testing
- **Agentic RAG**: Complex questions, reasoning needed, quality over speed

**Monitoring:**
- Check `processing_info` for timing, errors, and fallback status
- Regular RAG: ~1-3s, Agentic: ~2-5s

## Integration Examples

### Python
```python
import requests

def test_rag(query, agentic=False, authors=None, works=None):
    payload = {"query": query, "agentic": agentic}
    if authors: payload["authors"] = authors
    if works: payload["works"] = works

    return requests.post("http://localhost:8000/test", json=payload).json()

result = test_rag("What is grace?", agentic=True, authors=["augustine"])
```

### JavaScript
```javascript
async function testRag(query, options = {}) {
    const payload = {query, agentic: options.agentic || false};
    if (options.authors) payload.authors = options.authors;
    if (options.works) payload.works = options.works;

    return fetch('http://localhost:8000/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(r => r.json());
}

const result = await testRag("What is grace?", {
    agentic: true,
    authors: ['augustine']
});
```

## Troubleshooting

**Empty results:** Query too specific, try broader terms
**Slow responses:** Reduce `top_k`, use fewer `return_fields`, try regular mode
**AI errors:** Check `processing_info`, system falls back to search
**Unknown fields:** Use `/test/fields` to see available fields

**Debugging:** Start simple, check `processing_info`, compare modes

---

**Note:** Testing endpoint is experimental. No authentication required. Temporary sessions auto-cleanup.