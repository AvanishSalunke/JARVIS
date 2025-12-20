import os
from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PERSIST_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "jarvis_long_term_memory"

def _get_embedding_function():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in .env file.")
    return MistralAIEmbeddings(mistral_api_key=api_key)

def get_vector_store():
    """Initializes and returns the ChromaDB connection."""
    embeddings = _get_embedding_function()
    
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    return vector_store

def add_text_to_memory(text: str, vector_store: Chroma):
    """Saves text to the long-term database."""
    vector_store.add_texts([text])
    print(f"💾 Memory stored: {text}")

def search_memory(query: str, vector_store: Chroma) -> list[str]:
    """Finds relevant past memories."""
    # k=2 means "find the top 2 most relevant memories"
    docs = vector_store.similarity_search(query, k=2)
    return [doc.page_content for doc in docs]