from crewai import Agent
from tools import retriever_tool
from langchain_openai import ChatOpenAI

OPENAIGPT4TURBO = ChatOpenAI(
    model="gpt-4-turbo-preview"
)

# Creating a senior researcher agent with memory and verbose mode
researcher = Agent(
  role='Senior Security Researcher',
  goal='Uncover documentation that can help with technical issues related to Ledger products',
  verbose=True,
  memory=True,
  backstory=(
    "Driven by curiosity, you're at the forefront of"
    "cybersecurity applied to blockchain and an expert in Ledger products including the Ledger Nano S, Nano S Plus, Nano X, Ledger Stax and the Ledger Live app."
  ),
  tools=[retriever_tool],
  allow_delegation=False,
  llm=OPENAIGPT4TURBO
)

# Creating a writer agent with custom tools and delegation capability
writer = Agent(
  role='Writer',
  goal='Use documentation to solve technical issues.',
  verbose=True,
  memory=True,
  backstory=(
    "With a flair for simplifying complex topics, you"
    "are able to use documentation to answer the most complex technical questions about Ledger products."
  ),
  # tools=[retriever_tool],
  allow_delegation=False,
  llm=OPENAIGPT4TURBO
)

