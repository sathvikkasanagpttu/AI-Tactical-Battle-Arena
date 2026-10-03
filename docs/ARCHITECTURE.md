# Architecture

## Layers

### Presentation
Browser-based responsive tactical interface.

### API
FastAPI exposes game state, actions, analytics and history.

### Game Engine
Owns turns, movement validation, combat, healing and win conditions.

### AI Engine
Scores threats and targets, selects actions and uses A* pathfinding.

### Data Layer
SQLite stores matches, actions and explainable AI decisions.

## AI Decision Flow

```text
Battle State
   -> Target candidates
   -> Role priority
   -> Distance score
   -> Health score
   -> Tactical score
   -> Action selection
   -> Explainable decision
```

## Production Evolution

Replace SQLite with PostgreSQL, introduce Redis for active sessions, add JWT authentication, and separate game state into a dedicated service if multiplayer is introduced.
