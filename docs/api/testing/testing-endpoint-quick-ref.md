# Testing Endpoint Quick Reference

## Endpoints

### POST `/test` - Run Test Query
Compare Agentic vs Regular RAG systems

### GET `/test/fields` - Get Available Fields
List all fields that can be requested

## Quick Examples

### Minimal Request
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is salvation?"}'
```

### Full-Featured Request
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the Trinity",
    "agentic": true,
    "top_k": 3,
    "return_fields": ["record_id", "text", "authorid", "answer"]
  }'
```

### Get Available Fields
```bash
curl -X GET "http://localhost:8000/test/fields"
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | **required** | Your question/search text |
| `agentic` | boolean | `false` | Use Agentic RAG (true) or Regular RAG (false) |
| `top_k` | integer | `5` | Number of results to retrieve |
| `return_fields` | array | `["record_id"]` | Fields to include in response |

## Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Unique identifier |
| `text` | string | Content/paragraph text |
| `authorid` | string | Author identifier |
| `workid` | string | Work/book identifier |
| `versionid` | string | Version identifier |
| `sectionid` | string | Section identifier |
| `docid` | integer | Document ID |
| `knn_distance` | float | Similarity score |
| `refs` | array | References/citations |
| `link` | string | URL to source |
| `citation_text` | string | Formatted citation |
| `answer` | string | AI-generated response |

## Common Field Combinations

### Performance Testing
```json
{"return_fields": ["record_id", "knn_distance"]}
```

### Content Analysis  
```json
{"return_fields": ["record_id", "text", "authorid", "workid", "citation_text"]}
```

### AI Comparison
```json
{"return_fields": ["record_id", "text", "answer"]}
```

### Full Data Export
```json
{"return_fields": ["record_id", "text", "authorid", "workid", "knn_distance", "link", "answer"]}
```

## Response Structure

```json
{
  "query": "Your original query",
  "agentic_mode": true/false,
  "results": [
    {
      "field_name": "value"
    }
  ],
  "ai_answer": "AI response",
  "processing_info": {
    "mode": "agentic|regular",
    "processing_time_seconds": 1.23,
    "results_returned": 5,
    "sources_found": 8
  }
}
```

## Mode Comparison

| Feature | Regular RAG | Agentic RAG |
|---------|-------------|-------------|
| **Speed** | Faster (1-3s) | Slower (2-5s) |
| **Intelligence** | Basic | Advanced reasoning |
| **Consistency** | High | Variable |
| **Quality** | Good | Often better |
| **Use Case** | Simple queries | Complex questions |

## Tips

### When to Use Regular RAG
- Fast responses needed
- Simple, direct questions
- Bulk testing scenarios

### When to Use Agentic RAG  
- Complex, multi-part questions
- Need reasoning about the query
- Quality over speed

### Optimization
- Fewer fields = faster responses
- Lower `top_k` = faster processing
- Specific queries work better than vague ones

## Error Handling

- System automatically falls back to basic search if AI fails
- Check `processing_info` for error details
- `fallback_to_search: true` indicates fallback occurred
- Error messages appear in `agent_error` or `rag_error` fields