# Smart Library Assistant

A RAG-powered API server that helps retrieve and analyze Christian texts from CCEL (Christian Classics Ethereal Library). This system combines domain-specific retrieval with natural language understanding to answer specific and nuanced theological questions accurately and efficiently.

## Features

- OpenAI-powered embeddings for semantic search
- Manticore Search integration for vector search
- RAG (Retrieval-Augmented Generation) pipeline
- API endpoints for embedding, search, and query generation

## Prerequisites

- Python 3.8+
- Manticore Search server (already set up)
- OpenAI API key

## Setup

1. Clone the repository

```bash
git clone <repository-url>
cd smart-library-assistant
```

2. Set up virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables
   Copy the `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your OpenAI API key and database configuration.

## Running the Server

Start the server with:

```bash
python server.py
```

The server will start on http://localhost:8000

## API Endpoints

- `GET /` - Check API status
- `POST /embed/` - Generate embeddings for text
- `POST /search/` - Search for similar texts based on a query
- `POST /generate/` - Generate a response based on a query and context
- `POST /rag/` - Complete RAG pipeline: search + generate response

## Usage Example

To query the RAG endpoint:

```bash
curl -X POST "http://localhost:8000/rag/" \
  -H "Content-Type: application/json" \
  -d '{"query": "What does St. Augustine say about free will?"}'
```

## Architecture

The system works in the following steps:

1. User query is converted to an embedding using OpenAI's API
2. Embedding is used to search for relevant text passages in Manticore
3. Retrieved passages are sent as context to OpenAI's completion API
4. A comprehensive answer is generated and returned to the user
