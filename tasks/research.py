from crewai import Task
from tools import retriever_tool
from crew.researcher import researcher

# Research task
research_task = Task(
  description=(
    "Look into your Knowledge base to find the best answer to {topic}. Keep looking until you find a chunk that really answers the question in {topic}"
  ),
  expected_output='Two chunks from the Ledger technical documentation that answer {topic}',
  tools=[retriever_tool],
  agent=researcher,
  async_execution=False,
)