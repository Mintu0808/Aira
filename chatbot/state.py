from pydantic import BaseModel, Field
from typing import List
from langgraph.graph import MessagesState

class UserFact(BaseModel):
    category: str = Field(description="e.g., 'coding_preferences', 'interview_goals'")
    fact: str = Field(description="The concrete detail extracted from the text.")

class MemoryExtractorSchema(BaseModel):
    new_facts: List[UserFact] = Field(default=[])

class AgentConfiguredState(MessagesState):
    user_id: str
    thread_id: str
