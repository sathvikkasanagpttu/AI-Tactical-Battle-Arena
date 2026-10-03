from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import sqlite3, json, time, heapq, math, random

BASE = Path(__file__).resolve().parent
DB = BASE / "tactical_arena.db"
app = FastAPI(title="AI Tactical Battle Arena", version="1.0.0")

MAP_W, MAP_H = 10, 10
OBSTACLES = {(2,2),(2,3),(2,4),(5,2),(5,3),(5,4),(7,6),(7,7),(4,7),(5,7)}
game = {"turn": 1, "phase": "PLAYER", "winner": None, "last_ai": "Waiting for player action."}

UNITS = [
    {"id":"P1","team":"PLAYER","type":"Assault","x":1,"y":8,"hp":100,"max_hp":100,"damage":28,"range":2,"moves":3},
    {"id":"P2","team":"PLAYER","type":"Sniper","x":0,"y":9,"hp":75,"max_hp":75,"damage":38,"range":5,"moves":2},
    {"id":"P3","team":"PLAYER","type":"Medic","x":2,"y":8,"hp":85,"max_hp":85,"damage":12,"range":2,"moves":3},
    {"id":"P4","team":"PLAYER","type":"Scout","x":1,"y":7,"hp":70,"max_hp":70,"damage":20,"range":3,"moves":4},
    {"id":"A1","team":"AI","type":"Assault","x":8,"y":1,"hp":100,"max_hp":100,"damage":26,"range":2,"moves":3},
    {"id":"A2","team":"AI","type":"Sniper","x":9,"y":0,"hp":75,"max_hp":75,"damage":34,"range":5,"moves":2},
    {"id":"A3","team":"AI","type":"Medic","x":7,"y":1,"hp":85,"max_hp":85,"damage":10,"range":2,"moves":3},
    {"id":"A4","team":"AI","type":"Scout","x":8,"y":2,"hp":70,"max_hp":70,"damage":18,"range":3,"moves":4},
]

conn = sqlite3.connect(DB)
conn.executescript("""
CREATE TABLE IF NOT EXISTS matches(
 id INTEGER PRIMARY KEY AUTOINCREMENT, started_at REAL, ended_at REAL, result TEXT, turns INTEGER);
CREATE TABLE IF NOT EXISTS actions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, turn INTEGER, team TEXT,
 unit_id TEXT, action TEXT, target_id TEXT, damage INTEGER, created_at REAL);
CREATE TABLE IF NOT EXISTS ai_decisions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, turn INTEGER,
 unit_id TEXT, decision TEXT, reason TEXT, score REAL, created_at REAL);
""")
conn.close()
match_id = None

def reset():
    global UNITS, game, match_id
    UNITS = [
        {"id":"P1","team":"PLAYER","type":"Assault","x":1,"y":8,"hp":100,"max_hp":100,"damage":28,"range":2,"moves":3},
        {"id":"P2","team":"PLAYER","type":"Sniper","x":0,"y":9,"hp":75,"max_hp":75,"damage":38,"range":5,"moves":2},
        {"id":"P3","team":"PLAYER","type":"Medic","x":2,"y":8,"hp":85,"max_hp":85,"damage":12,"range":2,"moves":3},
        {"id":"P4","team":"PLAYER","type":"Scout","x":1,"y":7,"hp":70,"max_hp":70,"damage":20,"range":3,"moves":4},
        {"id":"A1","team":"AI","type":"Assault","x":8,"y":1,"hp":100,"max_hp":100,"damage":26,"range":2,"moves":3},
        {"id":"A2","team":"AI","type":"Sniper","x":9,"y":0,"hp":75,"max_hp":75,"damage":34,"range":5,"moves":2},
        {"id":"A3","team":"AI","type":"Medic","x":7,"y":1,"hp":85,"max_hp":85,"damage":10,"range":2,"moves":3},
        {"id":"A4","team":"AI","type":"Scout","x":8,"y":2,"hp":70,"max_hp":70,"damage":18,"range":3,"moves":4},
    ]
    game = {"turn":1,"phase":"PLAYER","winner":None,"last_ai":"Waiting for player action."}
    conn=sqlite3.connect(DB)
    cur=conn.execute("INSERT INTO matches(started_at,result,turns) VALUES(?,?,?)",(time.time(),"IN_PROGRESS",1))
    match_id=cur.lastrowid
    conn.commit(); conn.close()
reset()

class Action(BaseModel):
    unit_id: str
    action: str
    target_id: str | None = None
    x: int | None = None
    y: int | None = None

def alive(team):
    return [u for u in UNITS if u["team"]==team and u["hp"]>0]

def dist(a,b): return abs(a["x"]-b["x"])+abs(a["y"]-b["y"])

def neighbors(p):
    x,y=p
    for q in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0<=q[0]<MAP_W and 0<=q[1]<MAP_H and q not in OBSTACLES:
            yield q

def astar(start, goal):
    if start == goal: return [start]
    openq=[(0,start)]
    came={}; g={start:0}
    while openq:
        _,cur=heapq.heappop(openq)
        if cur==goal:
            path=[cur]
            while cur in came:
                cur=came[cur]; path.append(cur)
            return path[::-1]
        for nxt in neighbors(cur):
            ng=g[cur]+1
            if ng<g.get(nxt,9999):
                came[nxt]=cur; g[nxt]=ng
                f=ng+abs(nxt[0]-goal[0])+abs(nxt[1]-goal[1])
                heapq.heappush(openq,(f,nxt))
    return [start]

def log_action(team, unit, action, target=None, damage=0):
    conn=sqlite3.connect(DB)
    conn.execute("INSERT INTO actions(match_id,turn,team,unit_id,action,target_id,damage,created_at) VALUES(?,?,?,?,?,?,?,?)",
                 (match_id,game["turn"],team,unit["id"],action,target["id"] if target else None,damage,time.time()))
    conn.commit(); conn.close()

def log_ai(unit, decision, reason, score):
    conn=sqlite3.connect(DB)
    conn.execute("INSERT INTO ai_decisions(match_id,turn,unit_id,decision,reason,score,created_at) VALUES(?,?,?,?,?,?,?)",
                 (match_id,game["turn"],unit["id"],decision,reason,score,time.time()))
    conn.commit(); conn.close()

def ai_turn():
    players=alive("PLAYER")
    if not players: return
    game["phase"]="AI"
    decisions=[]
    for ai in alive("AI"):
        if not players: break
        # Score targets by low HP, proximity, and role priority.
        scored=[]
        for p in players:
            role_bonus={"Sniper":18,"Medic":14,"Assault":8,"Scout":5}[p["type"]]
            proximity=max(0,20-dist(ai,p)*3)
            low_hp=max(0,30-p["hp"]*0.3)
            score=role_bonus+proximity+low_hp
            scored.append((score,p))
        score,target=max(scored,key=lambda z:z[0])
        if dist(ai,target)<=ai["range"]:
            damage=ai["damage"]+random.randint(-4,4)
            target["hp"]=max(0,target["hp"]-damage)
            reason=f"Target priority {target['type']}; distance {dist(ai,target)}; attack opportunity detected."
            game["last_ai"]=f"{ai['type']} attacked {target['type']} for {damage} damage."
            log_action("AI",ai,"ATTACK",target,damage); log_ai(ai,"ATTACK",reason,round(score,1))
        else:
            path=astar((ai["x"],ai["y"]),(target["x"],target["y"]))
            steps=min(ai["moves"],max(1,len(path)-1))
            if steps:
                ai["x"],ai["y"]=path[steps]
            reason=f"No attack available; A* selected a {max(0,len(path)-1)}-step route toward {target['type']}."
            game["last_ai"]=f"{ai['type']} repositioned toward {target['type']}."
            log_action("AI",ai,"MOVE",target,0); log_ai(ai,"MOVE",reason,round(score*0.75,1))
    game["phase"]="PLAYER"
    game["turn"]+=1
    check_winner()

def check_winner():
    if not alive("PLAYER"):
        game["winner"]="AI"
    elif not alive("AI"):
        game["winner"]="PLAYER"
    if game["winner"]:
        conn=sqlite3.connect(DB)
        conn.execute("UPDATE matches SET ended_at=?,result=?,turns=? WHERE id=?",(time.time(),game["winner"],game["turn"],match_id))
        conn.commit(); conn.close()

@app.get("/",response_class=HTMLResponse)
def index():
    return HTMLResponse((BASE.parent/"frontend"/"index.html").read_text())

@app.get("/api/health")
def health(): return {"status":"healthy","service":"AI Tactical Battle Arena","version":"1.0.0"}

@app.get("/api/game")
def get_game():
    return {"game":game,"units":UNITS,"obstacles":[{"x":x,"y":y} for x,y in OBSTACLES]}

@app.post("/api/game/restart")
def restart():
    reset(); return get_game()

@app.post("/api/game/action")
def player_action(a: Action):
    if game["winner"]: raise HTTPException(400,"Match is already finished.")
    if game["phase"]!="PLAYER": raise HTTPException(400,"Wait for the AI turn.")
    unit=next((u for u in UNITS if u["id"]==a.unit_id and u["team"]=="PLAYER" and u["hp"]>0),None)
    if not unit: raise HTTPException(404,"Player unit not found.")
    if a.action=="ATTACK":
        target=next((u for u in UNITS if u["id"]==a.target_id and u["team"]=="AI" and u["hp"]>0),None)
        if not target: raise HTTPException(404,"Target not found.")
        if dist(unit,target)>unit["range"]: raise HTTPException(400,"Target is out of range.")
        damage=unit["damage"]
        target["hp"]=max(0,target["hp"]-damage)
        log_action("PLAYER",unit,"ATTACK",target,damage)
    elif a.action=="MOVE":
        if a.x is None or a.y is None or (a.x,a.y) in OBSTACLES or not (0<=a.x<MAP_W and 0<=a.y<MAP_H):
            raise HTTPException(400,"Invalid destination.")
        path=astar((unit["x"],unit["y"]),(a.x,a.y))
        if len(path)-1>unit["moves"]: raise HTTPException(400,"Destination is beyond movement range.")
        occupied={(u["x"],u["y"]) for u in alive("PLAYER")+alive("AI") if u["id"]!=unit["id"]}
        if (a.x,a.y) in occupied: raise HTTPException(400,"Destination occupied.")
        unit["x"],unit["y"]=a.x,a.y
        log_action("PLAYER",unit,"MOVE")
    elif a.action=="HEAL":
        target=next((u for u in UNITS if u["id"]==a.target_id and u["team"]=="PLAYER" and u["hp"]>0),None)
        if not target or unit["type"]!="Medic": raise HTTPException(400,"Medic can heal a living ally.")
        if dist(unit,target)>unit["range"]: raise HTTPException(400,"Ally is out of healing range.")
        healed=min(25,target["max_hp"]-target["hp"]); target["hp"]+=healed
        log_action("PLAYER",unit,"HEAL",target,healed)
    else: raise HTTPException(400,"Unknown action.")
    check_winner()
    if not game["winner"]: ai_turn()
    return get_game()

@app.get("/api/history")
def history():
    conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
    rows=conn.execute("SELECT * FROM matches ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return {"matches":[dict(r) for r in rows]}

@app.get("/api/analytics")
def analytics():
    conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
    matches=conn.execute("SELECT COUNT(*) c FROM matches").fetchone()["c"]
    wins=conn.execute("SELECT COUNT(*) c FROM matches WHERE result='PLAYER'").fetchone()["c"]
    actions=conn.execute("SELECT COUNT(*) c FROM actions").fetchone()["c"]
    damage=conn.execute("SELECT COALESCE(SUM(damage),0) s FROM actions WHERE team='PLAYER'").fetchone()["s"]
    ai=conn.execute("SELECT COUNT(*) c FROM ai_decisions").fetchone()["c"]
    conn.close()
    return {"games":matches,"wins":wins,"win_rate":round(wins/matches*100,1) if matches else 0,
            "player_damage":damage,"ai_decisions":ai,"actions":actions}

app.mount("/static",StaticFiles(directory=BASE.parent/"frontend"),name="static")
