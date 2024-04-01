from crewai import Task
from tools import retriever_tool
from crew.researcher import researcher

# Research task
research_task = Task(
  description=(
    """Look into your Knowledge base to find the best answer to {topic}. 
    Keep looking until you find a chunk that really answers the question in {topic}. 
    Discard the parts that are not useful. Make sure to always cite your sources by adding a plain URL link (no markdown)"""
  ),
  expected_output='The exact part of the documentation that answers: {topic}.',
  #tools=[retriever_tool],
  agent=researcher,
  async_execution=False,
)