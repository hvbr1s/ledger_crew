import os
from dotenv import main
from fastapi.security import APIKeyHeader
from system.prompts import INVESTIGATOR_PROMPT, SALES_ASSISTANT_PROMPT
from fastapi import FastAPI, HTTPException, Depends
from crew.agents import researcher, writer, sales_assistant
from tasks.list import research_issue, write, assist_customer
from tools.retrieve_tool import simple_retrieve
from utility.callback import print_agent_output
from crewai import Crew, Process
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import main
import json
import asyncio
import time
import boto3


# Initialize environment variables
main.load_dotenv()

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
    'BACKEND_API_KEY': access_secret_parameter('BACKEND_API_KEY'),
    'OPENAI_API_KEY': access_secret_parameter('OPENAI_API_KEY'),
    'PINECONE_API_KEY': access_secret_parameter('PINECONE_API_KEY'),
    'PINECONE_ENVIRONMENT': access_secret_parameter('PINECONE_ENVIRONMENT'),
    'COHERE_API_KEY': access_secret_parameter('COHERE_API_KEY')
}

# Set up boto3 session with AWS credentials
boto3.setup_default_session(
    aws_access_key_id=os.getenv('ACCESS_KEY_ID', env_vars['ACCESS_KEY_ID']),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY', env_vars['SECRET_ACCESS_KEY']),
    region_name='eu-west-3'
)

# Initialize backend API keys
server_api_key=env_vars['BACKEND_API_KEY']
API_KEY_NAME="Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if not api_key_header or api_key_header.split(' ')[1] != server_api_key:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return api_key_header

# Initialize OpenAI client & Embedding model
openai_key = env_vars['OPENAI_API_KEY']
openai_client = AsyncOpenAI(

    api_key=openai_key,
    
)

# Define query class
class Query(BaseModel):
    user_input: str
    user_id: str | None = None
    user_locale: str | None = None
    platform: str | None = None


# Initialize app
app = FastAPI()

# Create new Crew
def create_crew():
    """Factory function to create a new Crew."""
    return Crew(
        agents=[researcher, sales_assistant], 
        tasks=[research_issue, assist_customer], 
        process=Process.sequential,
        step_callback=lambda x: print_agent_output(x, "MasterCrew Agent"),
        share_crew=False,
        cache=False,
        memory=False
    )

# Agent handling function
async def agent(task):
    print(f"Processing task-> {task}")
    # Ready the crew
    crew = create_crew()
    # Kickoff!
    response = crew.kickoff(inputs={"topic": task})
    return response


# Initialize user state and periodic cleanup function
USER_STATES = {}
TIMEOUT_SECONDS = 3600  # 60 minutes

async def periodic_cleanup():
    while True:
        await cleanup_expired_states()
        await asyncio.sleep(TIMEOUT_SECONDS)

# Improved startup event to use asyncio.create_task for the continuous background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())

# Enhanced cleanup function with improved error logging
async def cleanup_expired_states():
    try:
        current_time = time.time()
        expired_users = [
            user_id for user_id, state in USER_STATES.items()
            if current_time - state['timestamp'] > TIMEOUT_SECONDS
        ]
        for user_id in expired_users:
            try:
                del USER_STATES[user_id]
                print("User state deleted!")
            except Exception as e:
                print(f"Error during cleanup for user {user_id}: {e}")
    except Exception as e:
        print(f"General error during cleanup: {e}")

# Set up tooling 
TOOLS = [
{
    "type": "function",
    "function": {
    "name": "knowledge",
    "description": "Technical Question API, this API makes a POST request to an external Knowledge Base with a technical question.",
    "parameters": {
        "type": "object",
        "properties": {
        "query": {
            "type": "string",
            "description": "The user's technical question."
        }
        },
        "required": ["query"],
        "async": True,
        "implementation": "async def knowledge(query):"
    }
    }
}
]

async def chat(chat):
    # Define the initial messages with the system's instructions
    messages = [
        {"role": "system", "content":INVESTIGATOR_PROMPT},
        {"role": "user", "content": chat}
    ]
    try:
        # Call the API to get a response
        res = await openai_client.chat.completions.create(
            temperature=0.0,
            model='gpt-4-turbo-preview',
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            timeout= 30.0,
        )
        
    except Exception as e:
        print(f"Something went wrong: {e}")
        res = "Snap! Something went wrong, please try again!"

    return res

async def ragchat(user_id, chat_history):

    res = await chat(chat_history)

    # Check for tool_calls in the response
    if res.choices[0].message.tool_calls is not None:
        print("Calling API!")
        tool_call_arguments = json.loads(res.choices[0].message.tool_calls[0].function.arguments)

        # Extract query
        function_call_query = tool_call_arguments["query"]
        print(f'API Query-> {function_call_query}')

        try:
            
                res = await agent(function_call_query)
                print(f"Query processed succesfully!")
                
        
        except Exception as e:
                print(f"OpenAI completion failed: {e}")
                return("Snap! Something went wrong, please ask your question again!")

        USER_STATES[user_id]['previous_queries'][-1]['assistant'] = res

        return res
    
    # Extract reply content
    elif res.choices[0].message.content is not None:
        reply = res.choices[0].message.content
        USER_STATES[user_id]['previous_queries'][-1]['assistant'] = reply

        return reply
    

# RAGChat route
@app.post('/agent') 
#async def react_description(query: Query, api_key: str = Depends(get_api_key)): 
async def react_description(query: Query): # to demonstrate the UI 

    # Deconstruct incoming query
    user_id = query.user_id
    user_input = query.user_input.strip()

    # Create a conversation history for new users
    convo_start = time.time()
    USER_STATES.setdefault(user_id, {
        'previous_queries': [],
        'timestamp': convo_start
    })

    USER_STATES[user_id]['previous_queries'].append({'user': user_input})
    previous_conversations = USER_STATES[user_id]['previous_queries'][-4:]

    # Format previous conversations for RAG
    formatted_history = ""
    for conv in previous_conversations:
        formatted_history += f"User: {conv.get('user', '')}\nAssistant: {conv.get('assistant', '')}\n"

    # Construct the query string with complete chat history
    chat_history = f"CHAT HISTORY: \n\n{formatted_history.strip()}"

    try:

        # Start RAG
        response = await ragchat(user_id, chat_history)     

        #Clean response
        cleaned_response = response.replace("**", "").replace("Manager", "'My Ledger'")

        # Print for debugging
        print(
            
            chat_history + "\n",
            response + "\n\n"
                
        )          
                        
        # Return response to user
        return {'output': cleaned_response}
    
    except Exception as e:

        print(f"Something went wrong: {e}")
        return{"output": "Sorry, something went wrong, please try again!"}
    

# Pinecone retrieval route
@app.post('/pinecone')
async def react_description(query: Query, api_key: str = Depends(get_api_key)):
    # Deconstruct incoming query
    user_input = query.user_input.strip()
    print(f'Simple RAG for query: {user_input}')

    try:
        # Start date retrieval and reranking
        data = await simple_retrieve(user_input)
        print(data)
        
    except Exception as e:
        print(f'Error retrieving data: {e}')
        data = "Couldn't reach my database, please try the query again."

    return data
    
# start command -> uvicorn aws:app --host 0.0.0.0 --port 8800
