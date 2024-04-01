from crewai import Agent

# Creating a writer agent with custom tools and delegation capability
investigator = Agent(
  role='Investigator',
  goal='Understand and summarize a technical issue.',
  verbose=True,
  memory=True,
  backstory=(
    "An investigator at heart, you're passionate about investigating and summarizing issues faced by Ledger users."
  ),
  # tools=[retriever_tool],
  allow_delegation=False,
)