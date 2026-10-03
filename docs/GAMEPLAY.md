# Gameplay Design

1. Select a player unit.
2. Attack an enemy within range, heal an ally with the Medic, or move to a reachable tile.
3. The AI evaluates every surviving player unit.
4. AI selects the highest-scoring target.
5. If the target is in range, AI attacks.
6. Otherwise, AI calculates an A* route and repositions.
7. The event is persisted.
8. The next player turn begins.
9. The battle ends when one team has no surviving units.

## Tactical Design

Snipers create long-range pressure. Medics create sustain. Scouts provide mobility. Assault units provide close-range damage.
