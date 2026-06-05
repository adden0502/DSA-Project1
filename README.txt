# Card Roguelike Prototype

## Project Overview

This project is a card-based roguelike game developed using Python and Pygame. The player explores a multi-floor dungeon, fights various enemies and bosses, collects items, and aims to achieve the highest score possible. The game combines dungeon exploration, turn-based combat, inventory management, and progression systems inspired by modern roguelike deck-building games.

---

## Project Structure

### main.py

The main entry point of the game.

Responsibilities:

* Controls scene transitions
* Manages title screen
* Handles map exploration
* Starts battles
* Displays rewards, events, and game-over screens
* Communicates with the score and leaderboard systems

---

### battle.py

Handles all battle-related logic.

Responsibilities:

* Turn management
* Card usage
* Drag-and-drop interactions
* Battle animations
* Enemy actions
* Undo system
* Damage and block calculations

Data Structure:

* Queue (Deque) for turn management

---

### player.py

Defines the player character.

Responsibilities:

* Health management
* Energy management
* Block management
* Deck management
* Drawing and discarding cards

---

### enemy.py

Defines all enemy and boss behaviors.

Responsibilities:

* Enemy AI
* Enemy intents
* Attack patterns
* Summoning mechanics
* Boss phase transitions

Algorithm:

* BFS-based ally search and support behavior

---

### card.py

Defines card objects used during battles.

Responsibilities:

* Card information
* Energy cost
* Damage values
* Block values
* Card effects

---

### map_screen.py

Implements the dungeon map.

Responsibilities:

* Room generation
* Path connections
* Floor progression
* Current position tracking

Data Structure:

* Graph

---

### item_system.py

Handles inventory and item effects.

Responsibilities:

* Item database
* Item rarity management
* Inventory management
* Treasure rewards
* Boss relic rewards

Data Structures:

* List
* Dictionary
* Tree-like inventory organization

---

### score_manager.py

Handles score calculation and leaderboard management.

Responsibilities:

* Score calculation
* Score logging
* Leaderboard storage
* Top score management

Algorithm:

* Heap-based Top-K ranking

---

### leaderboard.json

Stores leaderboard data.

Contents:

* Player name
* Final score
* Floor reached
* Bosses defeated
* Undo count

---

## Directory Layout

```text
project/
│
├── main.py
├── battle.py
├── player.py
├── enemy.py
├── card.py
├── map_screen.py
├── item_system.py
├── score_manager.py
│
├── leaderboard.json
│
└── assets/
    ├── images/
    ├── sounds/
    └── fonts/
```

---

## Main Features

### Dungeon Map System

* Multi-floor dungeon progression
* Branching paths with connected rooms
* Different room types:

  * Monster Room
  * Treasure Room
  * Event Room
  * Rest Room
  * Boss Room
* Graph-based map traversal

### Turn-Based Combat

* Card-based battle system
* Energy management
* Attack and defense cards
* Enemy intent display
* Multiple enemy encounters
* Boss battles with unique mechanics

### Undo System

* Rewind previous actions during battle
* Restores game state through reverse playback
* Allows strategic experimentation
* Implemented using a stack-based history system

### Enemy AI

* Multiple enemy types with different behaviors
* Support, defense, attack, and summoning patterns
* BFS-based decision support for ally protection and targeting

### Item and Relic System

* Collect passive items throughout the run
* Different rarity levels:

  * Common
  * Rare
  * Epic
  * Legendary
  * Boss Relics
* Treasure room rewards
* Event room rewards
* Boss-exclusive relic drops

### Boss System

Each floor contains a unique boss encounter:

* Goblin King
* Necromancer Lord
* Iron Colossus
* Twin Demons
* Time Watcher
* The Undoer

### Score and Leaderboard System

* Score earned from:

  * Clearing rooms
  * Defeating enemies
  * Defeating bosses
  * Reaching higher floors
  * Maintaining health
* Penalties for:

  * Undo usage
  * Rest room usage
* Persistent leaderboard storage
* Heap-based Top-K ranking system

---

## Data Structures and Algorithms

The project demonstrates the use of several core data structures and algorithms:

| Feature         | Data Structure / Algorithm       |
| --------------- | -------------------------------- |
| Dungeon Map     | Graph                            |
| Undo System     | Stack                            |
| Turn Management | Queue (Deque)                    |
| Inventory       | List, Dictionary, Tree Structure |
| Enemy AI        | BFS                              |
| Leaderboard     | Heap (Top-K)                     |

---

## Controls

### Map Screen

* Click connected rooms to move
* Open inventory through the Items button

### Battle Screen

* Drag attack cards onto enemies
* Drag defense cards upward to activate them
* End Turn button to finish the player's turn
* Undo button to rewind actions

### Reward Screens

* Click an item to select it
* Click an event option to choose a reward

---

## Technologies Used

* Python 3
* Pygame

---

## Learning Objectives

This project was created to demonstrate practical applications of data structures and algorithms within a game development environment. It integrates graph traversal, stack-based undo functionality, queue-based turn management, BFS-assisted AI behavior, inventory organization, and heap-based leaderboard ranking into a complete interactive system.

---