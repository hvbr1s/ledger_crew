import os
from anthropic import AsyncAnthropic
from dotenv import main
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, status, Depends
from crew.researcher import researcher
from crew.writer import writer
from tasks.research import research_task
from tasks.write import write_task
from crewai import Crew, Process
from pydantic import BaseModel

# Initialize environment variables
main.load_dotenv()

# Initialize backend API keys
server_api_key=os.environ['BACKEND_API_KEY'] 
API_KEY_NAME=os.environ['API_KEY_NAME'] 
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if not api_key_header or api_key_header.split(' ')[1] != server_api_key:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return api_key_header

# Define query class
class Query(BaseModel):
    user_input: str
    user_id: str | None = None
    user_locale: str | None = None
    platform: str | None = None

# Initialize Anthropic client
anthropic_client = AsyncAnthropic(
    
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    timeout=45,
)

# Forming the tech-focused crew with enhanced configurations
crew = Crew(
  agents=[researcher, writer],
  tasks=[research_task, write_task],
  process=Process.sequential  # Optional: Sequential task execution is default
)

# Initialize app
app = FastAPI()

# Agent handling function
async def agent(user_input):
    response = crew.kickoff(inputs={"topic": user_input})
    return response
    

# RAG route
@app.post('/gpt') 
async def react_description(query: Query, api_key: str = Depends(get_api_key)): 
    user_input = query.user_input.strip()
    print(f"Query received: {user_input}")
    # Process query
    res = await agent(user_input)
    print(f"Query processed: {res}")
    return {'output': res}

# Local start command: uvicorn app:app --reload --port 8800