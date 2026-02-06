from livekit.agents.tts import ChunkedStream, AudioEmitter
from livekit.agents import APIConnectOptions
from dotenv import load_dotenv
from kokoro import KPipeline
import numpy as np
import livekit.agents.utils as utils
import asyncio
from livekit.agents import llm, tts
from typing import AsyncIterable, Optional
import sys
from pathlib import Path

# Add src to path for relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tools import search_contact, create_or_list_tasks, add_note_to_contact, add_or_update_contact
from agent.agent import agent_brain
import json

class CustomLangGraphLLM(llm.LLM):
    def __init__(self, history: list[dict] = []):
        super().__init__() # initializes the event system (self._events = {} etc.) that LiveKit relies on for metrics, tool calls, function calling callbacks, etc.

        self.history = history
        #Tools list
        self.tools = [
            {
                "name": "search_contact",
                "description": "Search for a contact by name and return details including notes and tasks.",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"]
                }
            },
            {
                "name": "add_or_update_contact",
                "description": "Add a new contact or update an existing one by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "add_note_to_contact",
                "description": "Add a note to a contact by name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contact_name": {"type": "string"},
                        "note": {"type": "string"}
                    },
                    "required": ["contact_name", "note"]
                }
            },
            {
                "name": "create_or_list_tasks",
                "description": "Create a new task for a contact or list tasks. For create: provide task and due_date. For list: provide only contact_name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contact_name": {"type": "string"},
                        "task": {"type": "string"},
                        "due_date": {"type": "string"}
                    },
                    "required": ["contact_name"]
                }
            }
        ]
        
        self.tool_funcs = {
            "search_contact": search_contact,
            "add_or_update_contact": add_or_update_contact,
            "add_note_to_contact": add_note_to_contact,
            "create_or_list_tasks": create_or_list_tasks
        }  
    
    async def complete(self, prompt: str, **kwargs) -> AsyncIterable[str]:
        # Appends new user input to history
        self.history.append({"role": "user", "content": prompt})

        while True:

            # Call LangGraph agent
            result = await agent_brain.ainvoke({"history": self.history, "tools": self.tools})

            response_text = result["output_text"]

            self.history = result["history"] 

            # Check for tool calls 
            if "tool_calls" in result:
                tool_calls = result["tool_calls"]
                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"]["arguments"])
                    tool_func = self.tool_funcs.get(func_name)
                    if tool_func:
                        try:
                            tool_result = await tool_func(**args)
                            self.history.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "name": func_name,
                                "content": str(tool_result)
                            })
                        except Exception as e:
                            self.history.append({"role": "tool", "content": f"Error: {str(e)}"})
                continue # Re-invoke with tool results
            
            # Yield as stream (framework expects iterable tokens/chunks)
            # For voice, chunk into sentences for better flow
            sentences = response_text.split('. ') 
            for sentence in sentences:
                yield sentence.strip() + '. ' if not sentence.endswith('.') else sentence
                await asyncio.sleep(0.05) # Simulating streaming delay
    
    async def chat (self, messages: list[dict[str, str]], **kwargs) -> AsyncIterable[str]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        async for chunk in self.complete(prompt, **kwargs):
            yield chunk

class CustomKokoroTTS(tts.TTS):
    def __init__(self, lang_code='a', voice='af_nicole', speed=1.0, samplerate=24000):
        super().__init__(
            sample_rate=samplerate,
            num_channels=1,
            capabilities=tts.TTSCapabilities(streaming=False)  # Current TTS doesnt support streaming switch to modern api's like (ElevenLabs, OpenAI, Cartesia, PlayHT, etc.)
        )
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.speed = speed
        self._sample_rate = samplerate

    def synthesize(
        self, text: str, *, conn_options: Optional[APIConnectOptions] = None
    ) -> ChunkedStream:
        """Return a proper ChunkedStream so StreamAdapter can async-with it."""
        if not text or not text.strip():
            # Empty response → empty stream
            return ChunkedStream(
                tts=self,
                input_text="",
                conn_options=conn_options or APIConnectOptions(),
            )
        return KokoroChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options or APIConnectOptions(),
        )

class KokoroChunkedStream(ChunkedStream):
    """Custom ChunkedStream that runs Kokoro and pushes raw PCM to LiveKit"""

    async def _run(self, output_emitter: AudioEmitter) -> None:
        text = self._input_text
        if not text or not text.strip():
            output_emitter.end_input()
            await output_emitter.join()
            return

        # LiveKit handshake for raw PCM
        request_id = utils.shortuuid()
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=self._tts.sample_rate,      # 24000
            num_channels=1,
            mime_type="audio/pcm",
        )

        generator = self._tts.pipeline(
            text, voice=self._tts.voice, speed=self._tts.speed
        )

        for _, _, audio_np in generator:
            if audio_np.dtype == np.float32:
                audio_np = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)

            output_emitter.push(audio_np.tobytes())
            await asyncio.sleep(0.02)   # natural pacing

        # Finish
        output_emitter.flush()
        output_emitter.end_input()
        await output_emitter.join()