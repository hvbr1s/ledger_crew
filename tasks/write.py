from crewai import Task
from tools import retriever_tool
from crew.writer import writer

# Writing task with language model configuration
write_task = Task(
  description=(
    "Write a technical answer to {topic}. Make it easy to understand."
  ),
  expected_output='A short response that answers {topic}, written in a friendly and engaging tone. Make sure to always cite your sources by adding a plain URL link (no markdown)',
  #tools=[retriever_tool],
  agent=writer,
  async_execution=False,
  output_file='response.txt'  # Example of output customization
)