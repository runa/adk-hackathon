from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search

root_agent = Agent(
    name="basic_search_agent",
    model="gemini-2.0-flash",
    description="Agent to find property information using Google Search.",
    instruction="""Search websites for information about the base property.
    For the property sited EXACTLY in the address; ignore similar addresses.
    For each property datum, please cite the source. 
    Find last sold date and price; property features (like pool, garden, shed; renovations done or needed, etc). 
    Other information that could be useful: robberies, murders, fires,etc.
    Don't assume anything, only return facts""",
    output_key="website_data",
    tools=[google_search]
)

