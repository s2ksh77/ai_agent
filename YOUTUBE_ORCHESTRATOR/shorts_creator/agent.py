import os
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from env import OPENAI_API_KEY, REPLICATE_API_TOKEN
from .prompt import DESCRIPTION, INSTRUCTION
from .sub_agents.content_planner.agent import conent_planner_agent
from .sub_agents.content_maker.agent import content_maker_agent
from .sub_agents.content_maker.video_maker.agent import video_maker_agent
from .sub_agents.video_composer.agent import video_composer_agent

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

USE_VIDEO_MAKER = os.getenv("USE_VIDEO_MAKER", "true").lower() in {"1", "true", "yes", "y"}

tools = [AgentTool(agent=conent_planner_agent)]

if USE_VIDEO_MAKER:
    tools.append(AgentTool(agent=video_maker_agent))
else:
    tools.append(AgentTool(agent=content_maker_agent))
    tools.append(AgentTool(agent=video_composer_agent))

root_agent = Agent(
    name="ShortsCreatorAgent",
    model=LiteLlm(model="openai/gpt-4o"),
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    tools=tools,
)
