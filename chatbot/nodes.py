import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from .database import get_long_term_memories, save_new_memories
from .state import AgentConfiguredState, MemoryExtractorSchema
from .database import log_message_to_db

load_dotenv()

# Setup model brain
model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
)

def chatbot_node(state: AgentConfiguredState):
    past_memory_context = get_long_term_memories(state["user_id"])
    
    system_prompt = SystemMessage(content=(
        f"You are a helpful assistant. Here is your persistent database knowledge about the user:\n"
        f"{past_memory_context}\n"
        f"Subtly tailor your response using this information."
    ))
    
    full_messages = [system_prompt] + state["messages"]
    response = model.invoke(full_messages)

     # 🛠️ Log the newly generated AI response to the readable table
    log_message_to_db(state["thread_id"], state["user_id"], "assistant", response.content)
    return {"messages": [response]}

def memory_extractor_node(state: AgentConfiguredState):
    structured_llm = model.with_structured_output(
        MemoryExtractorSchema,
        method="json_mode",
    )
    
    last_user_message = state["messages"][-2].content if len(state["messages"]) >= 2 else ""
    last_ai_message = state["messages"][-1].content if len(state["messages"]) >= 1 else ""
    
    extraction_prompt = f"""
    Identify only durable user facts, preferences, and goals from this exchange.
    Return only valid JSON in this exact shape:
    {{"new_facts": [{{"category": "...", "fact": "..."}}]}}
    If there are no durable facts, return {{"new_facts": []}}.

    User: {last_user_message}
    Assistant: {last_ai_message}
    """
    
    extracted_data = structured_llm.invoke(extraction_prompt)
    if extracted_data.new_facts:
        saved_count = save_new_memories(state["user_id"], extracted_data.new_facts)
        print(f"\n[Postgres Saver]: Saved {saved_count} new facts.")
        
    return {}
