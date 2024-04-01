from crewai import Agent
from tools import retriever_tool

# Creating a writer agent with custom tools and delegation capability
writer = Agent(
  role='Writer',
  goal='Use documentation to solve technical issues.',
  verbose=True,
  memory=True,
  backstory=(
    "With a flair for simplifying complex topics, you"
    "are able to use documentation to answer the most complex technical questions about Ledger products"
  ),
  # tools=[retriever_tool],
  allow_delegation=False,
)
