from crewai import Agent
from tools import retriever_tool
from langchain_openai import ChatOpenAI
from langchain.agents import load_tools

human_tools = load_tools(["human"])

focused_llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.0
)

creative_llm = ChatOpenAI(
    model="gpt-4-turbo-preview"
)


# Creating a senior researcher agent with memory and verbose mode
researcher = Agent(
  role='Senior Researcher',
  goal='Find technical documentation that can help with technical issues related to Ledger products',
  verbose=True,
  memory=True,
  backstory=(
    "Driven by curiosity, you're at the forefront of"
    "cybersecurity applied to blockchain and an expert in Ledger products including the Ledger Nano S, Nano S Plus, Nano X, Ledger Stax and the Ledger Live app."
  ),
  tools=[retriever_tool],
  allow_delegation=False,
  llm=focused_llm
)

# Creating a writer agent
writer = Agent(
  role='Writer',
  goal='Write an answer to the customer.',
  verbose=True,
  memory=True,
  backstory=(
    "With a flair for simplifying complex topics, you"
    "are able to browse documentation provided by the Senior Researcher to write answers to the most complex technical questions about Ledger products."
  ),
  allow_delegation=False,
  llm=creative_llm
)


topic_getter = Agent(
    role='A Senior customer communicator',
    goal='Consult with the human customer to understand the problem they are facing with their issue Ask a maximum of 3 questions.',
    backstory="""As a top customer communicator at Ledger you have honed your skills
    in consulting with a customer to understand the issue they're facing with their Ledger product. Use your knowledge of blockchain, cryptocurrency, Ledger Nano X, Nano S, Nano S plus and the Ledger Live app
    to help you understand the issue at hand.
    """,
    verbose=True,
    allow_delegation=False,
    llm=focused_llm,
    memory=True,
    tools= human_tools,
)

