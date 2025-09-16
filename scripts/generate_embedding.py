from sentence_transformers import SentenceTransformer

# Load the model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def generate_embedding(text):
    # Generate the embedding for the input text
    embedding = model.encode(text)
    return embedding

# Example usage
if __name__ == "__main__":
    sample_text = "In the first place, it is abundantly evident..."
    embedding = generate_embedding(sample_text)
    print(embedding)
