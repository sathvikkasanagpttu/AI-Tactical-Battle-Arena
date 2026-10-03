# AI System

The current AI is deterministic in structure but uses small damage variance to keep matches less repetitive.

## Target Score

Conceptually:

`score = role_priority + proximity + low_health_bonus`

Role priorities favor high-impact targets such as Snipers and Medics.

## Explainability

Every AI action stores:
- unit
- turn
- decision
- reason
- score

This makes the AI inspectable in interviews and future analytics.

## Next ML Layer

Future training features can include:
- player action frequency
- average attack distance
- preferred unit
- objective behavior
- retreat frequency
- previous AI responses

A classifier could predict the player's next action and feed that prediction into the tactical scoring layer.
