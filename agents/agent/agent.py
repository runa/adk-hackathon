from google.adk.agents import SequentialAgent
from agent.agents.bridgeoutput_agent.agent import root_agent as bridgeoutput_agent
from agent.agents.google_search_agent.agent import root_agent as google_search_agent
from agent.agents.gmaps_agent.agent import root_agent as gmaps_agent
from agent.agents.report_writer_agent.agent import root_agent as report_writer_agent

root_agent = SequentialAgent(
    name="real_estate_agent_comparables",
    description="A real estate agent who can find comparables for a base property",
    sub_agents=[gmaps_agent, google_search_agent, bridgeoutput_agent, report_writer_agent],
)