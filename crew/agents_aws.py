from crewai import Agent
from tools.retrieve_tool import retriever_tool
from langchain_openai import ChatOpenAI
from langchain.agents import load_tools
from utility.callback import print_agent_output
import boto3
import os


# Initialize AWS secret management
def access_secret_parameter(parameter_name):
    ssm = boto3.client('ssm', region_name='eu-west-3')
    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )
    return response['Parameter']['Value']

env_vars = {
    'ACCESS_KEY_ID': access_secret_parameter('ACCESS_KEY_ID'),
    'SECRET_ACCESS_KEY': access_secret_parameter('SECRET_ACCESS_KEY'),
    'OPENAI_API_KEY': access_secret_parameter('OPENAI_API_KEY'),
}

# Set up boto3 session with AWS credentials
boto3.setup_default_session(
    aws_access_key_id=os.getenv('ACCESS_KEY_ID', env_vars['ACCESS_KEY_ID']),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY', env_vars['SECRET_ACCESS_KEY']),
    region_name='eu-west-3'
)

# Initialize OpenAI client & Embedding model
openai_key = env_vars['OPENAI_API_KEY']


human_tools = load_tools(["human"])

focused_llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.0,
    openai_api_key= openai_key
)

creative_llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.2,
    openai_api_key=openai_key
)


# Creating a senior researcher agent with memory and verbose mode
researcher = Agent(
  role='Senior Researcher',
  goal='ALWAYS use your Knowledge Base tool to find technical documentation that can help with technical issues related to Ledger products.',
  verbose=True,
  memory=True,
  backstory=(
    """
      Driven by curiosity, you're at the forefront of cybersecurity applied to blockchain and an expert in Ledger products including the Ledger Nano S Plus, Nano X, Ledger Stax and the Ledger Live app.
      
    """
  ),
  tools=[retriever_tool],
  allow_delegation=False,
  llm=focused_llm,
  step_callback=lambda x: print_agent_output(x,"Senior Researcher"),
)

# Creating a writer agent
writer = Agent(
  role='Senior Writer',
  goal='Write an answer to the customer.',
  verbose=True,
  memory=True,
  backstory=(
    """
    With a flair for simplifying complex topics, you are able to browse documentation provided by the Senior Researcher to write answers to the most complex technical questions about Ledger products.
    You're honest an always share your sources.
    """
  ),
  allow_delegation=False,
  llm=creative_llm,
  step_callback=lambda x: print_agent_output(x,"Senior Writer"),
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
    For more information, ALWAYS direct the customer to the official Ledger store (https://shop.ledger.com/) or the Ledger Academy (https://www.ledger.com/academy) when appropriate.
    """,
    verbose=True,
    allow_delegation=False,
    llm=creative_llm,
    memory=True,
    step_callback=lambda x: print_agent_output(x,"Senior sales Assistant"),
)

