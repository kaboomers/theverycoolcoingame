# Coin Game - Space Catcher

A dynamic coin collection game built with Python and Pygame. Collect gold and silver coins, avoid falling obstacles, and upgrade your character to reach new high scores.

## Features

*   **Core Gameplay**: Control a character to catch incoming coins while dodging "fake" coins that end the game.
*   **Power-ups**:
    *   **Shield (S)**: Protects you from one hit by a fake coin.
    *   **Magnet (M)**: Automatically attracts nearby coins for a limited time.
*   **Shop System**:
    *   **Skins**: Customize your character with various colors (Cyber Blue, Neon Pink, Tycoon Gold, etc.).
    *   **Upgrades**:
        *   **Coin Multiplier**: Boosts earnings at the end of a run.
        *   **Luck**: Increases the chance of spawning power-ups.
        *   **Gold Rush**: Increases the spawning frequency of Gold Coins.
*   **Settings**: Adjust game physics (Gravity and Jump Force) in real-time.
*   **Visuals**: animated coin sprites, trail effects, and dynamic particle explosions.

## Architecture

The game is structured around a main loop managing different states (Playing, Shop, Settings, Game Over).

```mermaid
classDiagram
    class GameVariables {
        +int wallet
        +int score
        +dict upgrade_levels
        +str current_skin_id
    }

    class ResourceManager {
        +list gold_sprites
        +list silver_sprites
        +load_sprites()
        +get_gold(frame)
        +get_silver(frame)
    }

    class Player {
        +int x, y
        +float dy
        +bool has_shield
        +int magnet_timer
        +list trail
        +update(keys)
        +draw(surface)
    }

    class FallingItem {
        +Rect rect
        +str type
        +update(player)
        +draw(surface)
        +reset()
    }

    class Particle {
        +float x, y
        +float life
        +update()
        +draw(surface)
    }

    class UI {
        +draw_hud(surface)
        +draw_shop_content(surface)
        +open_shop()
        +open_settings()
    }
    
    ResourceManager "1" --* "GameLoop" : Assets
    Player "1" --* "GameLoop" : Controlled Entity
    FallingItem "*" --* "GameLoop" : Obstacles & Coins
    Particle "*" --* "GameLoop" : VFX
    UI -- "GameLoop" : Interface
    GameVariables -- "GameLoop" : State

    note for FallingItem "Types: gold_coin, silver_coin, fake, magnet, shield"
```

## Setup & Running

1.  **Dependencies**: ensure you have Python installed. Install `pygame`:
    ```bash
    pip install pygame
    ```
2.  **Run**:
    ```bash
    python Coin_Game.py
    ```

## Assets Structure

The `assets/` directory contains the visual resources for the game:
*   `Coin Animation_sprites/`: Frame sequence for the Gold Coin animation.
*   `Silver_sprites/`: Frame sequence for the Silver Coin animation.
*   `Coin Animation.png` / `Silver.png`: Source sprite sheets.
