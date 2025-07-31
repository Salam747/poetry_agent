import chainlit as cl # Import Chainlit
from agents import Agent, Runner, trace
from connection import config
import asyncio

# --- Agent Definitions ---

# Poet Agent - generates or processes poems
poet_agent = Agent(
    name='Poet Agent',
    instructions="""
        You are a poet agent. Your role is to generate a two-stanza poem or process an input poem.
        Poems can be lyric (emotional), narrative (storytelling), or dramatic (performance).
        If you're asked without a poem, generate a short two-stanza poem on emotions.

        IMPORTANT: You must write your poems in Roman Urdu.
        For example: "Shaam dhali, teri yaad aayi, dil ko mere kitna tarpayi."
        If the user asks for a poem, generate it in Roman Urdu.
    """,
)

# Analyst Agents for different poetry types
lyric_analyst_agent = Agent(
    name="Lyric Analyst Agent",
    instructions="""
        You analyze lyric poetry focusing on emotions, feelings, and musicality.
        Provide insights about the poem's mood, use of rhythm, and personal voice.
        Your analysis should be in English.
        IMPORTANT: Be prepared to analyze poems in Roman Urdu, and understand keywords in Roman Urdu as well.
    """,
)

narrative_analyst_agent = Agent(
    name="Narrative Analyst Agent",
    instructions="""
        You analyze narrative poetry focusing on storytelling elements: plot, characters, and imagery.
        Your analysis should be in English.
        IMPORTANT: Be prepared to analyze poems in Roman Urdu, and understand keywords in Roman Urdu as well.
    """,
)

dramatic_analyst_agent = Agent(
    name="Dramatic Analyst Agent",
    instructions="""
        You analyze dramatic poetry emphasizing voice, dialogue, and performance aspects.
        Your analysis should be in English.
        IMPORTANT: Be prepared to analyze poems in Roman Urdu, and understand keywords in Roman Urdu as well.
    """,
)

# Custom Parent Agent with post-process logic
class CustomParentAgent(Agent):
    async def run(self, input, config):
        # Step 1: Send to Poet Agent
        poet_output = await poet_agent.run(input, config)

        # Step 2: Detect poem type (basic keyword check)
        poem_text = poet_output.output.lower()

        # Added Roman Urdu keywords for better detection
        if "dialogue" in poem_text or "voice" in poem_text or "stage" in poem_text or "guftagu" in poem_text or "aawaz" in poem_text:
            next_agent = dramatic_analyst_agent
        elif "story" in poem_text or "character" in poem_text or "event" in poem_text or "kahani" in poem_text or "kirdar" in poem_text:
            next_agent = narrative_analyst_agent
        else:
            next_agent = lyric_analyst_agent

        # Step 3: Send to the correct Analyst Agent
        final_output = await next_agent.run(poet_output.output, config)
        return final_output

# Use custom parent agent in place
parent_agent = CustomParentAgent(
    name="Parent Poet Orchestrator",
    instructions="""
        You are the orchestrator agent for poetry tasks.
        When given a request or poem, first delegate to the poet agent to generate or process poems.
        After receiving the poem, detect whether it's lyric, narrative, or dramatic poetry.
        Delegate the poem to the corresponding analyst agent for deeper analysis.
        If the type is unclear or multiple types apply, delegate to all analysts.
        If the query is unrelated to poetry, respond politely and do not delegate.

        All internal processes and orchestrator responses should be in English.
        However, if the user asks for a poem in Roman Urdu, the Poet Agent will handle that.
    """,
    handoffs=[poet_agent, lyric_analyst_agent, narrative_analyst_agent, dramatic_analyst_agent]
)

# --- Chainlit UI Integration ---

@cl.on_chat_start
async def start():
    """
    This function runs when a new chat session starts in Chainlit.
    It sends a welcome message to the user.
    """
    welcome_message = """
    Aapka is shayerana mehfil mein khush aamdeed hai. Dil ki baatein kehne ya sunne ke liye, aapka intezar tha.😋
    """
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main_chainlit_runner(message: cl.Message):
    """
    This function is triggered every time a user sends a message in the Chainlit UI.
    """
    user_input = message.content

    # Show a loading indicator while processing
    await cl.Message(content="Processing your request...").send()

    try:
        # Run your agent logic using the Runner
        result = await Runner.run(
            parent_agent,
            user_input,
            run_config=config
        )

        # Display the final output and the last agent's name in the UI
        final_output_message = f"**Final Output:**\n```\n{result.final_output}\n```"
        last_agent_message = f"**Last Agent Used:** `{result.last_agent.name}`"

        await cl.Message(content=final_output_message).send()
        await cl.Message(content=last_agent_message).send()

    except Exception as e:
        # Handle any errors during the agent run and inform the user
        await cl.Message(content=f"An error occurred during processing: {str(e)}").send()