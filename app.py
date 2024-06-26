import os
from dotenv import main
from system.prompts import INVESTIGATOR_PROMPT, SALES_ASSISTANT_PROMPT
from tools.retrieve_tool import simple_retrieve
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, Depends
from crew.agents import researcher, writer, sales_assistant
from tasks.list import research_issue, write, assist_customer
from crewai import Crew, Process
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Request
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import main
from datetime import datetime
import json
import asyncio
import time



# Initialize environment variables
main.load_dotenv()

# Initialize backend API keys
server_api_key=os.environ['BACKEND_API_KEY']  
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if not api_key_header or api_key_header.split(' ')[1] != server_api_key:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return api_key_header

# Initialize OpenAI client & Embedding model
openai_key = os.environ['OPENAI_API_KEY']
openai_client = AsyncOpenAI(api_key=openai_key)
gpt = 'gpt-4-turbo'

# Initialize Groq client
from groq import Groq
groq_client = Groq(
    api_key=os.environ["GROQ_API_KEY"],
)
llama = 'llama3-8b-8192'



# Define query class
class Query(BaseModel):
    user_input: str
    user_id: str | None = None
    user_locale: str | None = None
    platform: str | None = None


# Initialize app
app = FastAPI()

# Ready the crew
crew = Crew(
  agents=[researcher],
  tasks=[research_issue],
  process=Process.sequential,
  verbose= 1,
)

# Agent handling function
async def agent(task):
    print(f"Processing task-> {task}")
    response = crew.kickoff(inputs={"topic": task})
    return response


# Initialize user state and periodic cleanup function
USER_STATES = {}
TIMEOUT_SECONDS = 1800  # 30 minutes

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
            model=gpt,
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

    # Set clock
    timestamp = datetime.now().strftime("%B %d, %Y")

    res = await chat(chat_history)

    # Check for tool_calls in the response
    if res.choices[0].message.tool_calls is not None:
        print("Calling API!")
        tool_call_arguments = json.loads(res.choices[0].message.tool_calls[0].function.arguments)

        # Extract query
        function_call_query = tool_call_arguments["query"]
        print(f'API Query-> {function_call_query}')

        ##### OpenAI #####
        # retrieved_context = await simple_retrieve(function_call_query)
        retrieved_context =  res = await agent(function_call_query)
        troubleshoot_instructions = "CONTEXT: " + "\n" + timestamp + " ." + retrieved_context + "\n\n" + "----" + "\n\n" + "ISSUE: " + "\n" + function_call_query

        try:
                res = await openai_client.chat.completions.create( #with OpenAI
                #res = groq_client.chat.completions.create( #with Llama3
                    temperature=0.0,
                    model=gpt,
                    messages=[

                        {"role": "system", "content": SALES_ASSISTANT_PROMPT },
                        {"role": "user", "content": troubleshoot_instructions}

                    ],
                    timeout= 45.0
                )
                new_reply = res.choices[0].message.content
                print(f"Query processed succesfully!")
      
        ######  CrewAI  #######

        # try:

        #     res = await agent(function_call_query) # use CrewAI
        #     print(res)
        #     #new_reply = res.choices[0].message.content  
        #     print(f"Query processed succesfully!")
        
        except Exception as e:
                print(f"OpenAI completion failed: {e}")
                return("Snap! Something went wrong, please ask your question again!")

        USER_STATES[user_id]['previous_queries'][-1]['assistant'] = res

        return new_reply
    
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
    # locale = query.locale if query.locale else "eng"

    # Create a conversation history for new users
    convo_start = time.time()
    USER_STATES.setdefault(user_id, {
        'previous_queries': [],
        'timestamp': convo_start
    })

    USER_STATES[user_id]['previous_queries'].append({'user': user_input})
    previous_conversations = USER_STATES[user_id]['previous_queries'][-6:]

    # Format previous conversations for RAG
    formatted_history = ""
    for conv in previous_conversations:
        formatted_history += f"User: {conv.get('user', '')}\nAssistant: {conv.get('assistant', '')}\n"

    # Construct the query string with complete chat history
    chat_history = f"CHAT HISTORY: \n\n{formatted_history.strip()}"

    try:

        # Start RAG
        response = await ragchat(user_id, chat_history)
        print(f'Response received-> {response}')     

        #Clean response
        cleaned_response = response.replace("**", "").replace("Manager", "'My Ledger'")

        # Print for debugging
        log_entry = f"""
----------------{f"User ID: {user_id}"}----------------
Full query: {query}
Concise query: {user_input}
Chat history: {formatted_history.strip()}
Final Output: {cleaned_response}
---------------------------------------
"""
        print(log_entry)      
                        
        # Return response to user
        return {'output': cleaned_response}
    
    except Exception as e:

        print(f"Something went wrong: {e}")
        return{"output": "Sorry, something went wrong, please try again!"}
    

# UI
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="./static/BBALP00A.TTF")
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Local start command: uvicorn app:app --reload --port 8800
    
