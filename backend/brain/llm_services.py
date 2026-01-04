import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from brain.web_search import get_search_tool

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class Brain:
    def __init__(self):
        # 1. Initialize Groq (Llama 3.3 is very fast/smart)
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile", 
            temperature=0.3
        )
        
        # 2. Load Tools (Serper)
        self.tools = [get_search_tool()]

        # 3. Define the Agent Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are J.A.R.V.I.S, a helpful, witty, and precise AI assistant. "
                "You have access to a real-time 'web_search' tool. "
                "Use it whenever the user asks for current information (news, weather, dates, specific facts). "
                "If the question is personal, answer from memory. "
                "Always maintain a cool, British butler persona."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 4. Create the Agent
        # With langchain 0.2.16 (installed above), this function is guaranteed to exist
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # 5. Create the Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=True
        )

    def generate_response(self, user_text, chat_history=[], context=""):
        # 1. Convert Chat History
        formatted_history = []
        
        if context:
            formatted_history.append(SystemMessage(content=f"Long Term Memory Context: {context}"))

        for msg in chat_history:
            if isinstance(msg, dict):
                if msg.get('role') == 'human':
                    formatted_history.append(HumanMessage(content=msg.get('content')))
                else:
                    formatted_history.append(AIMessage(content=msg.get('content')))
            else:
                formatted_history.append(msg)
        
        try:
            # 2. Run the Agent
            response = self.agent_executor.invoke({
                "input": user_text,
                "chat_history": formatted_history
            })

            return response["output"]
            
        except Exception as e:
            print(f"❌ Brain Error: {e}")
            return "I apologize, sir. My neural pathways are encountering a critical error processing that request."

# Global Instance
_brain_instance = Brain()

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])
    return _brain_instance.generate_response(user_input, chat_history, memory_context)