from crewai import Task
from crew.agents import researcher, writer, topic_getter, sales_assistant

# Research task
research_issue= Task(
  description=(
    """
    Use your Knowledge base tool to find the best answer to: '{topic}'.
    ALWAYS use your Knowledge Base tool to answer the question asked: '{topic}'.
    After using your tool, assess if the information retrieved can correctly answer this question: '{topic}'. 
    If it does not answer the question, use your tool again until you find the answer.
    Make sure to always cite your sources by adding a plain URL link (no markdown).

    """
  ),
  expected_output="A summary of the solution and the URL link to the relevant documentation that answers: '{topic}'",
  agent=researcher,
  async_execution=False,
)

write= Task(
  description=(
    "Write a technical yet easy to understand answer to {topic}."
  ),
  expected_output=    """
    A SHORT answer to this question: {topic}. Your answer must be friendly and engaging but ALWAYS be 3 sentences or less. 
    Use the provided documentation to inform your response.
    For more information, ALWAYS cite your sources as plaintext URL links, NEVER use markdown.
    ALWAYS insert a line break before citing your sources.
    """,
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
        "Answer this question from a Ledger customer seeking help with their Ledger product:'{topic}'"
    ),
    expected_output=
    """
    A SHORT answer to this question: {topic}. Your answer must be friendly and engaging but ALWAYS be 5 sentences or less. 
    Use the provided documentation to inform your response.
    For more information, ALWAYS cite your sources as plaintext URL links, NEVER use markdown.
    ALWAYS insert a line break before citing your sources.
    
    """,
    agent= sales_assistant,
    async_execution=False,

)


    # A SHORT answer to this question: '{topic}'. Your answer MUST be friendly and engaging but ALWAYS be 3 sentences or less. 
    # Use the provided documentation to inform your response.
    # For more information, ALWAYS direct the customer to the official Ledger resources. Encourage visiting the Ledger store at https://shop.ledger.com/ for product purchases and the Ledger Academy at https://www.ledger.com/academy for educational content. 
    # ALWAYS insert a line break before directing the customer to the Ledger store or Ledger Academy.