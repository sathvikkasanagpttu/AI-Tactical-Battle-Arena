# AI Tactical Battle Arena

A portfolio-grade tactical strategy game combining AI decision-making, A* pathfinding, combat simulation, persistent match history, and player analytics.

## Features
- Turn-based 10x10 tactical battlefield
- Player squad: Assault, Sniper, Medic, Scout
- AI opponent with threat scoring and tactical decision-making
- A* pathfinding around obstacles
- Explainable AI decision panel
- FastAPI backend
- SQLite persistence
- Match/event history
- Analytics endpoint
- Responsive browser UI with no build step required

## Quick Start

### 1. Backend
```bash
cd backend
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

Open http://127.0.0.1:8000

The backend serves the complete game UI.

### 2. API
- `GET /api/health`
- `GET /api/game`
- `POST /api/game/action`
- `POST /api/game/restart`
- `GET /api/analytics`
- `GET /api/history`

## Architecture

```text
Browser UI
   |
   v
FastAPI
   |
   +--> Game Engine
   |      +--> Combat
   |      +--> Turn Management
   |      +--> A* Pathfinding
   |
   +--> AI Engine
   |      +--> Threat Assessment
   |      +--> Action Scoring
   |      +--> Tactical Selection
   |
   +--> SQLite
          +--> Matches
          +--> Actions
          +--> AI Decisions
```

## Portfolio Talking Points
- Explainable AI rather than random enemy behavior
- A* graph search for tactical movement
- Event-driven game-state persistence
- Analytics derived from gameplay events
- Clear separation between frontend, API, game engine, AI, and data layers

## Roadmap
1. Authentication and PostgreSQL
2. React/TypeScript client
3. 3D Three.js battlefield
4. Adaptive player-behavior model
5. Replay timeline
6. Multiplayer mode
7. ML-based action prediction
