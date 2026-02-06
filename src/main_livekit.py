from dotenv import load_dotenv
import sys
from pathlib import Path

from livekit import agents
from livekit.agents import Agent, JobContext, WorkerOptions
from livekit.plugins import assemblyai, silero
from livekit.agents.cli import run_app
from livekit.plugins.turn_detector.english import EnglishModel

# Add src to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

from plugins.custom_plugins import CustomLangGraphLLM, CustomKokoroTTS

load_dotenv(".env.local") # LOADS OPENROUTER API KEY

class VoiceAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            Keep responses concise and natural for spoken dialgoue. Use the conversation history for context.
            Be friendly and helpful."""
        )

async def entrypoint(ctx: JobContext):
    # Create the session with custom LLM and TTS
    vad=silero.VAD.load()
    turn_detection=EnglishModel()
    stt = assemblyai.STT()
    llm=CustomLangGraphLLM()
    tts=CustomKokoroTTS()
    
    session = agents.AgentSession(
        vad=vad,
        turn_detection=turn_detection,
        stt=stt,
        llm=llm,
        tts=tts,
    )

    agent = VoiceAgent()

    await session.start(
        room=ctx.room,  # This connects to the job's room  
        agent=agent
        )

    await session.say(
    text="Hello! I'm your mini CRM assistant. How can I help you today?",
    allow_interruptions=True  # Optional: Allows user to interrupt the greeting
)

if __name__ == "__main__":
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="VoiceAgent"
    )
    run_app(opts)