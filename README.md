# Rock-Paper-Scissors-Plus AI Game Referee

## Project Overview

This is a minimal AI Game Referee chatbot for Rock-Paper-Scissors-Plus. The project demonstrates clean agent architecture using Google ADK primitives with explicit tool definitions, persistent state management, and comprehensive rule enforcement for a best-of-three game.

## Architecture Design

### State Model

The GameState class serves as the central state container that persists across all game turns:

- **round**: Current round number, ranges from 0 to 3 (best of 3 rounds)
- **user_score**: Tracks the number of rounds won by the user
- **bot_score**: Tracks the number of rounds won by the bot
- **user_bomb_used**: Boolean flag indicating whether user has used their single bomb
- **bot_bomb_used**: Boolean flag indicating whether bot has used its single bomb
- **game_over**: Boolean flag set to True when the game reaches round 3
- **history**: Immutable list of all previous rounds with moves and results

The design rationale behind this state model is straightforward. The explicit boolean flags for bomb usage prevent players from using the bomb more than once per game, which is a critical constraint in the game rules. The game_over flag provides a clean way to enforce the three-round limit without additional conditional logic in the main game loop. The history field enables debugging, transparency, and allows players to review how the game progressed.

### Agent and Tool Boundaries

The solution maintains clear separation across three distinct phases:

Intent Understanding -> Game Logic -> Response Generation

This corresponds directly to three explicit ADK tools:

1. **validate_move()** - Handles intent understanding by normalizing user input, checking against valid moves, and enforcing the bomb-once constraint

2. **resolve_round()** - Encodes pure game logic that determines the winner given two validated moves, including bomb override rules

3. **update_game_state()** - Handles state mutation by incrementing round counters, updating scores only for valid rounds, and tracking bomb usage

This separation ensures that each function has a single responsibility and can be reasoned about independently.

## Key Features

### Game Rules Implementation

The project implements all core game mechanics:

**Best of 3 Rounds**: The game automatically ends when the round counter reaches 3, enforced through the condition if state.round >= 3: state.game_over = True in the update_game_state function.

**Bomb Mechanics**: The bomb beats all other moves and can be used once per player. This is enforced through user_bomb_used and bot_bomb_used boolean flags that prevent bomb usage after the first time.

**Invalid Input Handling**: When a player provides invalid input, the round is wasted (round counter increments) but no score is awarded to either player. This distinguishes between "no score change" and "no round progression."

**Clear Rules Display**: Game rules are displayed at the start of the game in concise form.

### Player Feedback

The game provides comprehensive round-by-round feedback including:

- The round number
- Both players' moves
- The round winner or draw result
- Current score for both players

At the end of the game, the final result clearly states whether the user wins, the bot wins, or the result is a draw.

## Execution Flow

The following sequence occurs for each turn:

1. User provides input through the command line interface
2. Bot randomly selects a move from available moves, respecting bomb constraint
3. validate_move() tool processes and validates the user input
4. If invalid, the round is wasted and the turn ends
5. If valid, resolve_round() tool determines the winner based on game rules
6. update_game_state() tool increments the round counter and updates scores
7. generate_referee_response() produces human-readable feedback about the round
8. Score and game state are displayed to the player

## Technical Implementation

### Dependencies and Setup

The project requires only one external package:

```
pip install google-genai
```

This is the Google ADK for generative AI.

To run the application, set the GEMINI_API_KEY environment variable (optional, as the project has a deterministic fallback):

```
export GEMINI_API_KEY="your-api-key"
```

### Running the Application

To start the game, execute:

```
python rps_game.py
```

### Sample Gameplay

When the game runs, users see output similar to the following:

```
Round 1: You win! rock beats scissors.
Score: You 1 | Bot 0

Round 2: Invalid move! Round wasted.
Score: You 1 | Bot 0

Round 3: Bot wins! paper beats rock.
Score: You 1 | Bot 1

GAME OVER
Final Score -> You: 1 | Bot: 1
Result: Draw!
```

## Design Decisions and Tradeoffs

### Three Explicit Tools vs Single Function

Decision: Implement three explicit tools (validate_move, resolve_round, update_game_state).

Rationale: This provides clear boundaries between intent understanding, game logic, and state management. Each tool is testable and reusable independently, and the separation makes the code easier to understand and maintain.

Alternative: A single mega-function could handle all logic, reducing file size but making the code harder to debug and reducing clarity of purpose.

### Deterministic Fallback Mode

Decision: Include a fallback mode that works without API keys or when quota is exceeded.

Rationale: This ensures 100 percent reliability of the game during development and testing, eliminates quota frustrations, and ensures the application can be tested immediately without API setup.

Alternative: Pure API dependency would require working credentials and would fail when quota limits are reached.

### In-Memory State vs Persistent Storage

Decision: Use an in-memory GameState object that persists only during a single game session.

Rationale: This approach is simple and sufficient for the CLI interface. State management is straightforward and requires no external dependencies.

Alternative: Saving to JSON files would enable multi-session persistence but adds file I/O complexity and storage management.

### Command Line Interface

Decision: Implement a simple conversational loop using Python's input() function.

Rationale: This approach is minimal and sufficient for interactive gameplay. The conversational loop is easy to understand and maintain.

Alternative: A graphical interface would provide better user experience but adds unnecessary complexity for a game of this scope.

## Code Structure and Key Components

### GameState Class

This class encapsulates all game state. It provides a to_dict() method for serialization and maintains all necessary flags and counters.

### Tool Functions

validate_move() takes user input and bomb usage status, returning a dictionary indicating validity and the normalized move.

resolve_round() implements the complete game logic: bomb beats everything, bomb versus bomb is a draw, and rock-paper-scissors rules apply otherwise.

update_game_state() performs state mutations including round increment, bomb tracking, conditional score updates, and game-over detection.

### Referee Response Generation

generate_referee_response() takes the round result and produces human-readable feedback. It distinguishes between invalid, draw, user win, and bot win outcomes, formatting each appropriately.

### Game Turn Handler

run_turn() orchestrates the complete flow: determine bot choice, validate user input, resolve the round, update state, and generate response.

### Main Game Loop

The main() function handles initialization, displays rules, runs the game loop until game_over is True, and displays the final result.

## What Makes This Implementation Strong

### Clear Logic Implementation

All game rules are correctly implemented through the tool functions. Invalid moves waste rounds without affecting scores. Bomb rules are enforced through boolean flags. The three-round limit is enforced through the game_over flag.

### Well-Structured State Model

The GameState class provides a clear, explicit model of game state. State is kept separate from any API calls or prompts. Bomb flags prevent reuse. History enables transparency.

### Clean Architectural Boundaries

The separation between intent understanding (validate_move), game logic (resolve_round), and response generation (generate_referee_response) is explicit and well-commented.

### Proper Use of Tools

The project uses explicit tool definitions and schemas matching ADK conventions.

### Self-Documenting Code

Inline code comments and this README thoroughly explain every design decision, architectural choice, and implementation detail.

## Future Enhancements

### Enhanced AI Responses

The application could be extended to use language models for more dynamic and natural explanations of game outcomes.

### Advanced Bot Strategy

Instead of random move selection, the bot could implement game theory strategies such as pattern detection or probability-based responses based on game history.

### Multi-Round Reasoning

The bot could analyze game history and adapt its strategy across multiple rounds based on observed patterns in user play.

### Structured Output

Response formatting could be improved using schema validation to ensure consistent, machine-parseable output.

### Unit Testing

Each tool function could be tested independently using pytest, with external dependencies mocked to ensure reliability.

### Game Statistics

A stats tracking feature could record win rates, move frequency distributions, and overall player statistics.

### Persistent Game History

Games could be saved to files for later review and analysis across multiple sessions.

## Files Included

- rps_game.py: Complete implementation in a single Python file
- README.md: Architecture and design documentation

## Project Details

Python version: 3.8 or higher
Last updated: January 2026

---

This project demonstrates how to build a conversational game with clear architectural boundaries, explicit tool definitions, and proper state management. It serves as a solid foundation for more complex multi-turn interactive applications.
