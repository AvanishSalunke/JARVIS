import os
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool

def get_search_tool():
    # Serper needs SERPER_API_KEY in .env
    search = GoogleSerperAPIWrapper()
    return Tool(
        name="web_search",
        func=search.run,
        description="Search the web for current events, news, facts, or specific information."
    )