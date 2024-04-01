from crewai import Agent
from tools import retriever_tool

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
  allow_delegation=True,
)
