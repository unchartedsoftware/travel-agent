# AI Trip Planner

An AI-powered trip planning application that helps users plan safe routes considering weather conditions.

## Project Structure

```
ai-trip-agent/
├── client/          # Vue.js frontend application
│   ├── src/        # Source files for the client
│   ├── public/     # Public assets
│   └── ...         # Other client configuration files
└── server/         # Python backend
    ├── src/        # Source directory
    │   └── travel_agent/  # Python package
    │       ├── __init__.py
    │       └── agent.py   # AI agent for route planning
    ├── main.py     # FastAPI server
    └── ...         # Backend configuration files
```

## Development Setup

### Prerequisites
- Node.js 18 or higher
- Python 3.12.0 or higher
- [pyenv](https://github.com/pyenv/pyenv) (recommended for Python version management)

### Client (Vue.js Frontend)
```bash
# Install dependencies
cd client
npm install

# Start development server
npm run dev
```

### Server (Python Backend)
```bash
# Set up Python environment
cd server
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies in development mode
pip install -e .

# Set up environment variables (create a .env file)
cp .env.example .env
# Edit .env with your API keys

# Start the FastAPI server
python main.py
```

The FastAPI server will start on http://localhost:8000. You can access the API documentation at http://localhost:8000/docs.

Required API Keys:
- Google Maps API key
- OpenWeatherMap API key
- OpenAI API key

## Scripts

- `npm run client:dev` - Start the client development server (runs on http://localhost:5173)
- `npm run client:build` - Build the client for production
- `npm run client:preview` - Preview the client production build
