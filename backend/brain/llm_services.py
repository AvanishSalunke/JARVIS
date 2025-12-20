import os
from dotenv import load_dotenv  # <--- This was missing!
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# Load the API Key from your .env file
load_dotenv()

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    """
    1. Prepares the context (memories).
    2. Builds the prompt.
    3. Sends everything to Mistral.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        return "Error: Mistral API Key is missing. Please check your .env file."

    # Initialize the Model
    llm = ChatMistralAI(
        mistral_api_key=api_key, 
        model="mistral-large-latest", 
        temperature=0.7
    )

    # Format the long-term memory into a string
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])

    # The System Prompt
    system_instruction = f"""
    You are Jarvis, an advanced AI assistant. 
    
    ### Long-Term Memory (Facts you know):
    {memory_context}

    ### Instructions:
    - Answer helpfully and briefly.
    - If the answer is in the Long-Term Memory, use it.
    """

    # Build the conversation structure
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder(variable_name="history"), 
        ("human", "{input}")
    ])

    # Create and run the chain
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "history": chat_history,
        "input": user_input
    })

    return response