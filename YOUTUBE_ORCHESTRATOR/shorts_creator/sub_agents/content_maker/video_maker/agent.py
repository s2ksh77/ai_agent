from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import DESCRIPTION, INSTRUCTION
from .tools import generate_video


video_maker_agent = Agent(
    name="VideoMakerAgent",
    model=LiteLlm(model="openai/gpt-4o"),
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    output_key="video_maker_output",
    tools=[
        generate_video,
    ],
)
