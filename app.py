# app.py

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.wildperudo import WildPerudoGame
from src.player import HumanPlayer, FirstOrderPlayer
from src.game import Bid
import uvicorn
from typing import Optional, Dict
import uuid

app = FastAPI()

# Set up templates
templates = Jinja2Templates(directory="templates")

# In-memory storage for games
games: Dict[str, WildPerudoGame] = {}


class BidModel(BaseModel):
    count: int
    face: int


class GameState(BaseModel):
    game_id: str
    players: Dict[str, list]
    current_bid: Optional[BidModel]
    current_player: str


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/game/{game_id}/state")
def get_game_state(game_id: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    players_dice = {player.name: player.dice.values for player in game.players}
    players_scores = {player.name: game.scores[player.name] for player in game.players}
    current_bid = (
        BidModel(count=game.current_bid.count, face=game.current_bid.face)
        if game.current_bid
        else None
    )
    return {
        "game_id": game_id,
        "players": players_dice,
        "scores": players_scores,
        "current_bid": current_bid,
        "current_player": game.players[game.current_player_idx].name,
        "round_number": game.round_number,
    }


@app.post("/start_game", response_class=HTMLResponse)
def start_game(request: Request):
    game_id = str(uuid.uuid4())
    human_player = HumanPlayer(name="You", num_dice=5)
    ai_player = FirstOrderPlayer(name="AI", num_dice=5)
    players = [human_player, ai_player]
    game = WildPerudoGame(players)
    games[game_id] = game

    # Roll dice for the first round
    game.start_new_round()

    game_state = get_game_state(game_id)
    return templates.TemplateResponse(
        "game.html", {"request": request, "game_id": game_id, "game_state": game_state}
    )


@app.post("/game/{game_id}/challenge", response_class=HTMLResponse)
def challenge(request: Request, game_id: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    challenger = game.players[game.current_player_idx]

    # Resolve the challenge
    game.resolve_challenge(challenger)

    # Start a new round and roll dice
    game.start_new_round()

    game_state = get_game_state(game_id)
    return templates.TemplateResponse(
        "game.html", {"request": request, "game_id": game_id, "game_state": game_state}
    )


@app.post("/game/{game_id}/bid", response_class=HTMLResponse)
async def make_bid(
    request: Request, game_id: str, count: int = Form(...), face: int = Form(...)
):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player = game.players[game.current_player_idx]
    if not isinstance(player, HumanPlayer):
        raise HTTPException(status_code=400, detail="Not your turn")

    # Player makes a bid
    game.current_bid = Bid(count=count, face=face)
    # Advance to AI player
    game.current_player_idx = (game.current_player_idx + 1) % len(game.players)

    # AI's turn
    game.play_turn()

    # Update game state
    game_state = get_game_state(game_id)
    return templates.TemplateResponse(
        "game.html", {"request": request, "game_id": game_id, "game_state": game_state}
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
