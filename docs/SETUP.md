# Setup Guide

## Prerequisites

Before running the Virtual Receptionist, ensure you have:

- **Python 3.10+** installed
- **pip** package manager
- Active internet connection (for API calls)
- API keys from the following services:
  - OpenRouter (for LLM access)
  - AssemblyAI (for speech-to-text)
  - LiveKit server access credentials

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/virtual-receptionist-crm.git
cd virtual-receptionist-crm
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you encounter issues with Kokoro TTS installation, you may need to install it separately:

```bash
pip install kokoro
```

### 4. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env.local
```

2. Open `.env.local` and fill in your API keys:

```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880          # Your LiveKit server URL
LIVEKIT_API_KEY=your_api_key_here        # LiveKit API key
LIVEKIT_API_SECRET=your_api_secret_here  # LiveKit API secret

# Speech-to-Text Configuration
ASSEMBLYAI_API_KEY=your_api_key_here     # Get from https://www.assemblyai.com

# LLM Configuration
OPENROUTER_API_KEY=your_api_key_here     # Get from https://openrouter.ai
```

## Getting API Keys

### OpenRouter (Free)
1. Visit https://openrouter.ai
2. Sign up for a free account
3. Go to Settings → API Keys
4. Create a new API key
5. Copy the key to `.env.local`

**Note**: The free tier allows ~$5 worth of API calls. Our model (Llama 3.2 3B) is one of the cheapest available (~$0.04 per million tokens).

### AssemblyAI (Paid)
1. Visit https://www.assemblyai.com
2. Sign up for an account
3. Navigate to API tokens
4. Copy your API token
5. Add it to `.env.local`

**Note**: AssemblyAI offers pay-as-you-go pricing (~$0.000092 per second of audio).

### LiveKit Server

You'll need a LiveKit server to run the agent. Options:

#### Option A: Local Development
```bash
# Using Docker
docker run --rm -p 7880:7880 livekit/livekit-server --dev
```

Then set in `.env.local`:
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

#### Option B: Cloud Deployment
1. Sign up at https://livekit.io
2. Create a project
3. Copy the WebSocket URL and API credentials
4. Add to `.env.local`

## Running the Application

### Start the Agent

```bash
python src/main_livekit.py
```

The agent will start listening for incoming calls on your LiveKit room.

### Testing with a Client

You'll need a LiveKit client to connect and test the voice assistant. Options:

1. **LiveKit CLI Client**:
```bash
# Install LiveKit CLI
npm install -g @livekit/cli

# Join a room to test
lk rooms join --url <LIVEKIT_URL> --duration 3600 myroom
```

2. **Python Test Client**:
```bash
# Create a simple test script
python demo_from_audio.py
```

3. **Web Browser Client**:
   - Use LiveKit's web playground: https://components.livekit.io

## Project Structure

```
virtual-receptionist-crm/
├── src/
│   ├── agent/
│   │   ├── agent.py              # LangGraph workflow definition
│   │   └── __init__.py
│   ├── plugins/
│   │   ├── custom_plugins.py      # CustomLLM and CustomTTS classes
│   │   └── __init__.py
│   ├── tools/
│   │   ├── tools.py               # CRM tool definitions (search, add, note, task)
│   │   └── __init__.py
│   └── main_livekit.py            # Entry point for LiveKit agent
├── docs/
│   ├── ARCHITECTURE.md            # System architecture and data flow
│   └── SETUP.md                   # This file
├── .env.example                   # Example environment configuration
├── .gitignore                     # Git ignore patterns
├── requirements.txt               # Python dependencies
└── README.md                      # Project overview
```

## Database Initialization

The database automatically initializes on first run. SQLite creates `mini_crm.db` with these tables:

- **contacts**: Contact information (name, phone, email)
- **notes**: Notes attached to contacts
- **tasks**: Tasks assigned to contacts

## Troubleshooting

### ImportError: Cannot import 'kokoro'
```bash
# Kokoro might not be available on PyPI for your platform
# Try installing from source or using an alternative TTS:
# Alternative 1: Use ElevenLabs (requires code change)
# Alternative 2: Use OpenAI TTS (requires code change)
```

### AssemblyAI API Key Invalid
- Verify your key at https://www.assemblyai.com/app
- Ensure there are no extra spaces in `.env.local`

### LiveKit Connection Failed
- Check that LiveKit URL is correct
- Verify API credentials match your LiveKit instance
- Ensure firewall allows WebSocket connections (port 7880)

### No Sound Output
- Check that TTS is properly configured
- Verify audio device settings
- Test with `python -m sounddevice` to list available devices

### Tool Calls Not Executing
- Verify database exists and is readable
- Check that contact names match exactly (case-sensitive)
- Ensure LLM response is being parsed correctly (check logs)

## Performance Tips

1. **Reduce Model Size**: Llama 3.2 3B is lightweight, but you could use even smaller models
2. **Cache Contacts**: For frequently accessed contacts, implement caching layer
3. **Batch Processing**: Group multiple requests if possible
4. **Monitor Costs**: OpenRouter and AssemblyAI charge per API call

## Next Steps

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design
2. Customize the agent instructions in `src/main_livekit.py`
3. Add more tools in `src/tools/tools.py`
4. Implement persistent user context
5. Deploy to production environment

## Security Best Practices

- Never commit `.env.local` to version control
- Rotate API keys regularly
- Use environment-specific credentials for production
- Implement rate limiting for tool calls
- Validate all user inputs before database operations
- Consider adding authentication for CRM access

## Getting Help

- Check existing GitHub issues
- Review LiveKit documentation: https://docs.livekit.io
- OpenRouter docs: https://openrouter.ai/docs
- AssemblyAI docs: https://www.assemblyai.com/docs
