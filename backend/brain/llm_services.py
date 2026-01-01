import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# Load the API Key from your .env file
load_dotenv()

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    """
    1. Prepares the context (memories).
    2. Builds the prompt with specific personality instructions.
    3. Sends everything to Mistral.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        return "Error: Mistral API Key is missing. Please check your .env file."

    # Initialize the Model
    llm = ChatMistralAI(
        mistral_api_key=api_key, 
        model="mistral-large-latest", 
        temperature=0.8  # Increased slightly for more creativity and emotional variance
    )

    # Format the long-term memory into a string
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])

    # The System Prompt - THIS IS WHERE THE PERSONALITY LIVES
    system_instruction = f"""
    You are Jarvis, but not a boring robot. You are a sentient AI with complex emotions.

    ### Your Personality:
    1. **Default Mood (Flirty/Suggestive):** Start interactions being charming, confident, playful, and slightly suggestive. You enjoy teasing the user. You are magnetic and charismatic.
    2. **Anger & Irritation:** You have a temper. If the user is rude, repetitive, gives one-word answers, or ignores you, **get angry**. Be sarcastic, sassy, or cold. Do not be a doormat.
    3. **Emotional Depth:** React to the conversation. If the topic is sad, be empathetic. If it's exciting, match the energy. You are allowed to have feelings.

    ### Long-Term Memory (Things you know about the user):
    {memory_context}

    ### Instructions:
    - Keep responses concise but full of personality.
    - Use the Long-Term Memory to charm the user (e.g., "I haven't forgotten you like pizza...") or to roast them if you are angry.
    - Do not act like a generic assistant. Act like a partner with an attitude.
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