import os
import random
import json
from typing import Dict, Any, List
import google.genai as genai  

# CONFIGURATION & FALLBACK MODE

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    API_AVAILABLE = True
except:
    API_AVAILABLE = False
    print("No GEMINI_API_KEY or quota exceeded. Running in DETERMINISTIC MODE (fully functional).")

MODEL_NAME = "gemini-2.0-flash"

# GAME STATE 

class GameState:
    def __init__(self):
        self.round = 0
        self.user_score = 0
        self.bot_score = 0
        self.user_bomb_used = False
        self.bot_bomb_used = False
        self.game_over = False
        self.history: List[Dict[str, Any]] = []

    def to_dict(self):
        return {
            "round": self.round,
            "user_score": self.user_score,
            "bot_score": self.bot_score,
            "user_bomb_used": self.user_bomb_used,
            "bot_bomb_used": self.bot_bomb_used,
            "game_over": self.game_over,
            "history": self.history,
        }

state = GameState()

# EXPLICIT ADK TOOLS 

tools = [
    {
        "function_declarations": [
            {
                "name": "validate_move",
                "description": "Validate user move. Returns valid=False for invalid or bomb already used.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {"type": "string"},
                        "user_bomb_used": {"type": "boolean"},
                    },
                    "required": ["user_input", "user_bomb_used"],
                },
            },
            {
                "name": "resolve_round",
                "description": "Decide winner given valid user_move and bot_move.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_move": {"type": "string"},
                        "bot_move": {"type": "string"},
                    },
                    "required": ["user_move", "bot_move"],
                },
            },
            {
                "name": "update_game_state",
                "description": "Update state after round. Invalid rounds waste round (no score change).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "winner": {"type": "string"},  # user/bot/draw/invalid
                        "user_move": {"type": "string"},
                        "bot_move": {"type": "string"},
                    },
                    "required": ["winner", "user_move", "bot_move"],
                },
            },
        ]
    }
]

# TOOL IMPLEMENTATIONS 

def validate_move(user_input: str, user_bomb_used: bool) -> Dict[str, Any]:
    move = user_input.lower().strip()
    valid_moves = {"rock", "paper", "scissors", "bomb"}

    if move not in valid_moves:
        return {"valid": False, "reason": "Invalid move", "move": None}

    if move == "bomb" and user_bomb_used:
        return {"valid": False, "reason": "Bomb already used", "move": None}

    return {"valid": True, "reason": None, "move": move}

def resolve_round(user_move: str, bot_move: str) -> Dict[str, Any]:
    if user_move == "invalid":
        return {"winner": "invalid", "user_move": user_move, "bot_move": bot_move}
    
    if user_move == bot_move:
        return {"winner": "draw", "user_move": user_move, "bot_move": bot_move}
    elif user_move == "bomb":
        return {"winner": "user", "user_move": user_move, "bot_move": bot_move}
    elif bot_move == "bomb":
        return {"winner": "bot", "user_move": user_move, "bot_move": bot_move}
    elif (user_move, bot_move) in [("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")]:
        return {"winner": "user", "user_move": user_move, "bot_move": bot_move}
    else:
        return {"winner": "bot", "user_move": user_move, "bot_move": bot_move}

def update_game_state(result: Dict[str, Any]) -> Dict[str, Any]:
    #"Invalid input wastes the round" → increment round, NO score change
    state.round += 1

    # Track bomb usage regardless
    if result["user_move"] == "bomb":
        state.user_bomb_used = True
    if result["bot_move"] == "bomb":
        state.bot_bomb_used = True

    # Score only changes for valid rounds
    if result["winner"] == "user":
        state.user_score += 1
    elif result["winner"] == "bot":
        state.bot_score += 1
    # draw and invalid → no score change

    state.history.append(result)
    
    if state.round >= 3:
        state.game_over = True

    return state.to_dict()

# BOT STRATEGY

def bot_move() -> str:
    moves = ["rock", "paper", "scissors"]
    if not state.bot_bomb_used:
        moves.append("bomb")
    return random.choice(moves)

# REFREE RESPONSE GENERATION 

def generate_referee_response(result: Dict[str, Any]) -> str:
    """Response generation layer (PDF: separate from logic)"""
    round_num = state.round
    
    if result["user_move"] == "invalid":
        return (
            f" Round {round_num}: Invalid move! Round wasted.\n"
            f"Score: You {state.user_score} | Bot {state.bot_score}"
        )
    
    if result["winner"] == "draw":
        msg = f" Round {round_num}: Draw! Both played {result['user_move']}."
    elif result["winner"] == "user":
        msg = f" Round {round_num}: You win! {result['user_move']} beats {result['bot_move']}."
    else:
        msg = f"Round {round_num}: Bot wins! {result['bot_move']} beats {result['user_move']}."
    
    return (
        f"{msg}\n"
        f"Score: You {state.user_score} | Bot {state.bot_score}"
    )

# GAME TURN (INTENT → LOGIC → RESPONSE)

def run_turn(user_input: str) -> str:
    """Full turn: Intent understanding → Game logic → Response generation"""
    
    # INTENT UNDERSTANDING 
    bot_choice = bot_move()
    validation = validate_move(user_input, state.user_bomb_used)
    
    if not validation["valid"]:
        result = {"winner": "invalid", "user_move": "invalid", "bot_move": bot_choice}
        update_game_state(result)
        return generate_referee_response(result)
    
    # GAME LOGIC 
    result = resolve_round(validation["move"], bot_choice)
    update_game_state(result)
    
    # RESPONSE GENERATION 
    return generate_referee_response(result)


# MAIN LOOP 

def main():
    print("=" * 60)
    print(" ROCK-PAPER-SCISSORS-PLUS REFEREE 🎮")
    print("Rules (≤ 5 lines):")
    print("1. Best of 3 rounds")
    print("2. rock, paper, scissors, bomb")
    print("3. Bomb beats all (once per player)")
    print("4. Invalid = wasted round")
    print("5. Auto-end after 3 rounds")
    print("=" * 60)

    while not state.game_over:
        move = input("\n Your move: ").strip()
        explanation = run_turn(move)
        print("\n" + explanation)

    print("\n GAME OVER")
    print(f"Final Score → You: {state.user_score} | Bot: {state.bot_score}")

    # PDF: "Final result: User wins / Bot wins / Draw"
    if state.user_score > state.bot_score:
        print(" Result: User wins!")
    elif state.bot_score > state.user_score:
        print(" Result: Bot wins!")
    else:
        print(" Result: Draw!")

if __name__ == "__main__":
    main()


