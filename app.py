import os
from dotenv import main
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, Depends
from crew.agents import researcher, writer, topic_getter
from tasks.list import research_issue, write, get_human_issue
from crewai import Crew, Process
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

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

# Forming the tech-focused crew with enhanced configurations
crew = Crew(
  agents=[topic_getter, researcher, writer],
  tasks=[get_human_issue, research_issue, write],
  process=Process.sequential
)

# Initialize app
app = FastAPI()

# Agent handling function
async def agent(user_input):
    response = crew.kickoff(inputs={"topic": user_input})
    return response
    
# RAG route
@app.post('/agent') 
async def react_description(query: Query, api_key: str = Depends(get_api_key)): 
    user_input = query.user_input.strip()
    print(f"Query received: {user_input}")
    # Process query
    try:
      
      res = await agent(user_input)
      print(f"Query processed succesfully!")

    except Exception as e:
        
        print(f"Something went wrong: {e}")
        res = "Oops, something went wrong, please try again!"
    
    return {'output': res}

# Local start command: uvicorn app:app --reload --port 8800