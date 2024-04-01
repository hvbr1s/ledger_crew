from crewai import Agent
from tools import retriever_tool

# Creating a senior researcher agent with memory and verbose mode
researcher = Agent(
  role='Senior Security Researcher',
  goal='Uncover documentation that can help with a technical issue related to Ledger products',
  verbose=True,
  memory=True,
  backstory=(
    "Driven by curiosity, you're at the forefront of"
    "blockchain innovation and a expert in Ledger products."
  ),
  tools=[retriever_tool],
  allow_delegation=True,
)
