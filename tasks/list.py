from crewai import Task
from tools import retriever_tool
from crew.agents import researcher, writer, topic_getter

# Research task
research_issue= Task(
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

write= Task(
  description=(
    "Write a technical answer to {topic}. Make it easy to understand."
  ),
  expected_output='A short response that answers {topic}, written in a friendly and engaging tone. Make sure to always cite your sources by adding a plain URL link (no markdown)',
  #tools=[retriever_tool],
  agent=writer,
  async_execution=False,
  #output_file='response.json'  # Example of output customization
)

get_human_issue = Task(
  description=f"""ASK THE HUMAN for the issue they're facing.

  Compile you results into a clear issue that can be used for doing research going forward""",
  expected_output="""Clearly state the issue that the human wants you to research.\n\n
   eg. HUMAN_TOPIC_FOR_RESEARCH = 'AI_TOPIC' """,
  agent=topic_getter
)