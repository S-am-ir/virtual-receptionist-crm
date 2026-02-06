# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (User)                                │
│                    (Voice Call/Audio Stream)                        │
└────────────┬────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LIVEKIT SERVER                                  │
│         (WebRTC-powered voice communication platform)               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  AgentSession Container                                      │  │
│  │                                                               │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │  │
│  │  │   VAD       │    │   STT       │    │   TTS       │     │  │
│  │  │  (Silero)   │    │(AssemblyAI) │    │  (Kokoro)   │     │  │
│  │  │  Voice      │    │  Speech to  │    │  Text to    │     │  │
│  │  │  Activity   │    │  Text       │    │  Speech     │     │  │
│  │  │  Detection  │    │             │    │             │     │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘     │  │
│  │         │                  │                  │              │  │
│  │         └──────────────────┴──────────────────┘              │  │
│  │                    │                                         │  │
│  │                    ▼                                         │  │
│  │         ┌──────────────────┐                               │  │
│  │         │  CustomLLM       │                               │  │
│  │         │  (LangGraph-     │                               │  │
│  │         │   based Wrapper) │                               │  │
│  │         └──────────────────┘                               │  │
│  │                    │                                         │  │
│  └────────────────────┼──────────────────────────────────────┘  │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────┐
        │    OPENROUTER LLM API            │
        │  (Meta Llama 3.2 3B Instruct)    │
        │                                  │
        │ - Processes conversation history │
        │ - Executes tool calls            │
        │ - Generates contextual responses │
        └──────────────────────────────────┘
                        │
                        ├──────────────────────┐
                        │                      │
                        ▼                      ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │   AGENT BRAIN        │  │   TOOL EXECUTION     │
        │  (LangGraph Workflow)│  │                      │
        │                      │  │ ┌────────────────┐   │
        │ - Manages state      │  │ │ Contact        │   │
        │ - Routes logic       │  │ │ Management     │   │
        │ - Handles tools      │  │ │ ────────       │   │
        │ - Updates history    │  │ │ • Search       │   │
        │                      │  │ │ • Add/Update   │   │
        │                      │  │ │ • List         │   │
        │                      │  │ └────────────────┘   │
        │                      │  │                      │
        │                      │  │ ┌────────────────┐   │
        │                      │  │ │ Note           │   │
        │                      │  │ │ Management     │   │
        │                      │  │ │ ────────       │   │
        │                      │  │ │ • Add note     │   │
        │                      │  │ │ • Retrieve     │   │
        │                      │  │ └────────────────┘   │
        │                      │  │                      │
        │                      │  │ ┌────────────────┐   │
        │                      │  │ │ Task           │   │
        │                      │  │ │ Management     │   │
        │                      │  │ │ ────────       │   │
        │                      │  │ │ • Create       │   │
        │                      │  │ │ • List         │   │
        │                      │  │ │ • Update due   │   │
        │                      │  │ └────────────────┘   │
        └──────────────────────┘  └──────────────────────┘
                   │                      │
                   └──────────┬───────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │   SQLite Database    │
                    │  (mini_crm.db)       │
                    │                      │
                    │ Tables:              │
                    │ • contacts           │
                    │ • notes              │
                    │ • tasks              │
                    └──────────────────────┘
```

## Data Flow

### 1. **User Input (Voice)**
   - User speaks in the voice call
   - VAD (Voice Activity Detection) captures the speech
   - Audio is transmitted to the STT engine

### 2. **Speech-to-Text (STT)**
   - AssemblyAI transcribes audio to text
   - Transcription is passed to LLM

### 3. **LLM Processing**
   - OpenRouter LLM receives transcribed text + conversation history
   - LLM can make tool calls based on user intent
   - Tools are passed as available functions to the LLM

### 4. **Tool Execution**
   - If LLM decides to use a tool (e.g., search_contact), it outputs a tool call
   - Agent brain intercepts and executes the tool against SQLite database
   - Tool results are added back to conversation history
   - LLM generates final response with tool results as context

### 5. **Text-to-Speech (TTS)**
   - LLM response is passed to Kokoro TTS
   - Audio is synthesized and streamed back to user via LiveKit

## Component Details

### **Input Processing**
- **VAD (Silero)**: Detects when user is speaking
- **STT (AssemblyAI)**: Transcribes speech to structured text
- **Turn Detector**: Manages conversation turns

### **Intelligence Layer**
- **CustomLangGraphLLM**:
  - Wraps OpenRouter API
  - Handles tool schema formatting
  - Manages conversation history
  - Routes tool calls to executor

- **Agent Brain (LangGraph)**:
  - Stateful workflow orchestration
  - Tool invocation and response handling
  - Output generation

### **Tool Layer**
- **search_contact**: Fuzzy search for contacts with associated notes/tasks
- **add_or_update_contact**: Create or modify contact information
- **add_note_to_contact**: Attach notes to contacts
- **create_or_list_tasks**: Task creation and listing per contact

### **Database**
- **SQLite (mini_crm.db)**:
  - Lightweight, file-based persistence
  - Tables: contacts, notes, tasks
  - Foreign key relationships for data integrity

### **Output Layer**
- **CustomKokoroTTS**:
  - Text synthesis using Kokoro pipeline
  - Sentence-level streaming for natural pacing
  - PCM audio encoding for LiveKit compatibility

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Communication** | LiveKit | WebRTC-based voice infrastructure |
| **Speech-to-Text** | AssemblyAI | Transcription service |
| **LLM** | OpenRouter (Llama 3.2) | Language understanding & generation |
| **Orchestration** | LangGraph | Stateful workflow management |
| **Text-to-Speech** | Kokoro | Voice synthesis |
| **VAD** | Silero | Voice activity detection |
| **Database** | SQLite | Persistent CRM data |
| **Runtime** | Python | Codebase implementation |

## State Management

```
AgentState {
  history: List[dict]         # Full conversation history
  next_action: str            # Router decision point
  output_text: str            # Text to be spoken
  tool_calls: List[dict]      # Extracted tool calls
  tools: List[dict]           # Available tool schemas
}
```

The state is maintained through:
1. **Conversation History**: All user/assistant/tool messages
2. **Tool Context**: Available functions and their definitions
3. **Output Buffer**: Current response being synthesized

## Error Handling Flow

```
Tool Execution
  │
  ├─ Success: Add tool result to history
  │
  └─ Error: Log error message to history
      └─> LLM receives error context
          └─> Can retry or explain to user
```

## Security Considerations

- **API Keys**: Stored in `.env.local` (not committed)
- **Database**: Local SQLite (no network exposure)
- **Tool Constraints**: Tools only operate on database, no system access
- **Rate Limiting**: Managed by external API providers (OpenRouter, AssemblyAI)

## Performance Characteristics

- **Latency**:
  - STT: ~1-3 seconds (network dependent)
  - LLM Response: ~500ms - 2s (depends on response length)
  - TTS: ~500ms - 1s (depends on text length)
  - Tool Execution: ~50-200ms (depends on query complexity)

- **Concurrency**:
  - Single call at a time (LiveKit AgentSession)
  - Can be scaled with multiple worker instances

## Future Improvements

1. **Streaming TTS**: Integrate ElevenLabs/Cartesia for faster TTS
2. **Error Context**: More granular error handling and recovery
3. **Persistent Context**: Link sessions to user profiles
4. **Advanced Tools**: Email integration, calendar management
5. **Multi-language**: Language detection and switching
6. **Analytics**: Call logging, tool usage tracking
