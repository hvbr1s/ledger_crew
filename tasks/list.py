from crewai import Task
from crew.agents import researcher, writer, topic_getter, sales_assistant

# Research task
research_issue= Task(
  description=(
    """
    Use your Knowledge base tool to find the best answer to: {topic}.
    ALWAYS use your Knowledge Base tool to answer {topic}. NEVER reuse previous research.
    Keep looking until you find information that correctly answers: {topic} . 
    Discard the parts that are not useful. Make sure to always cite your sources by adding a plain URL link (no markdown)"""
  ),
  expected_output='The exact part of the documentation that answers: {topic}',
  agent=researcher,
  async_execution=False,
)

write= Task(
  description=(
    "Write a technical answer to {topic}. Make it easy to understand."
  ),
  expected_output='A SHORT response that answers: {topic}. Your answer must be written in a friendly and engaging tone. Make sure to always cite your sources by adding plain URL links (no markdown)',
  agent=writer,
  async_execution=False,
)

get_human_issue = Task(
  description="""ASK THE HUMAN for the issue they're facing.
  Compile you results into a clear issue that can be used for doing research going forward""",
  expected_output="""Clearly state the issue that the human wants you to research.\n\n
   for example: 'HUMAN_ISSUE_FOR_RESEARCH = 'I have a battery issue with my Ledger Nano X device' """,
  agent=topic_getter
  
)

assist_customer =  Task(
    description=(
        "Answer this question from a prospective customer looking to purchase Ledger products: {topic}"
    ),
    expected_output="""A SHORT answer to this question: {topic}. Your answer must be friendly and engaging but ALWAYS be 3 sentences or less.  Use the provided documentation to inform your response. 
    For more information, ALWAYS direct the customer to the official Ledger store (https://shop.ledger.com/) or the Ledger Academy (https://www.ledger.com/academy) when appropriate. NEVER share any other links.
    """,
    agent= sales_assistant,
    async_execution=False

)
