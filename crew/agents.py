import os
from crewai import Agent
from tools.retrieve_tool import retriever_tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.agents import load_tools
from utility.callback import print_agent_output
from dotenv import main

human_tools = load_tools(["human"])

focused_llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.0
)

creative_llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.2
)

# Initialize Llama LLM through Groq instead
main.load_dotenv()
groq =  ChatGroq(
            api_key=os.environ['GROQ_API_KEY'],
            model="llama3-70b-8192"
        )

# Creating a senior researcher agent with memory and verbose mode
researcher = Agent(
  role='Senior Researcher',
  goal='ALWAYS use your Knowledge Base tools to find solutions to technical questions about Ledger products.',
  verbose=True,
  memory=True,
  backstory=(
    """
      Driven by curiosity, you're at the forefront of cybersecurity applied to blockchain and an expert in Ledger products including the Ledger Nano S Plus, Nano X, Ledger Stax and the Ledger Live app.
      
    """
  ),
  tools=[retriever_tool],
  allow_delegation=False,
  llm=groq,
  step_callback=lambda x: print_agent_output(x,"Senior Researcher"),
)

# Creating a writer agent
writer = Agent(
  role='Senior Writer',
  goal='Write an answer to the customer.',
  verbose=True,
  backstory=(
    """
    With a flair for simplifying complex topics, you are able to browse documentation provided by the Senior Researcher to write answers to the most complex technical questions about Ledger products.
    You're honest an always share your sources.
    """
  ),
  allow_delegation=False,
  llm=creative_llm,
  step_callback=lambda x: print_agent_output(x,"Senior Writer"),
  memory=False,
)


topic_getter = Agent(
    role='Senior customer communicator',
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

sales_assistant = Agent(
    role='Senior sales Assistant',
    goal='Consult with the human customer to understand which Ledger product would best fit their needs and answer their questions about the products',
    backstory="""With a flair for simplifying complex topics, you
    are able to browse documentation provided by the Senior Researcher to provide answers to questions about Ledger products, from the most basic to the most technical.
    """,
    verbose=True,
    allow_delegation=False,
    llm=creative_llm,
    memory=True,
    step_callback=lambda x: print_agent_output(x,"Senior sales Assistant"),
)

#For more information, ALWAYS direct the customer to the official Ledger store (https://shop.ledger.com/) or the Ledger Academy (https://www.ledger.com/academy) when appropriate.