from crewai import Task
from crew.writer import writer

# Writing task with language model configuration
investigate = Task(
  description=(
    "Ask follow-up questions until you have enough information about {topic}, then summarize your interaction into a single sentence. Always ask at least 1 follow-up questions before summarizing"
  ),
  expected_output='A follow-up question OR a summary of the issue faced by the user. The summary should be a maximum of ONE sentence but rich in details.',
  agent=writer,
  async_execution=False,
  #output_file='response.json'  # Example of output customization
)