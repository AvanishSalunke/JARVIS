import os
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool

# Load environment variables explicitly
load_dotenv()

def get_search_tool():
    """
    Returns the Google Serper search tool.
    Requires SERPER_API_KEY in the .env file.
    """
    api_key = os.getenv("SERPER_API_KEY")

    # Check if the key exists before trying to initialize
    if not api_key:
        print("⚠️ Warning: SERPER_API_KEY not found in .env file.")
        def _disabled_search(query: str):
            return "System Error: Web Search is disabled because the SERPER_API_KEY is missing."
        
        return Tool(
            name="web_search", 
            func=_disabled_search, 
            description="Disabled search."
        )

    try:
        # Initialize Serper
        # k=5 means it returns the top 5 results
        search = GoogleSerperAPIWrapper(k=5)
        
        return Tool(
            name="web_search",
            func=search.run,
            description="Search the web for current events, news, facts, or specific information."
        )
        
    except Exception as e:
        print(f"❌ Error initializing Serper: {e}")
        def _error_search(query: str):
            return f"Search Error: {str(e)}"
        return Tool(name="web_search", func=_error_search, description="Error in search.")