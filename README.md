# 🌀 THE LABYRINTH: CORE DESCENT

Welcome, Agent. You have discovered the **Labyrinth**, a persistent, file-system-based dungeon crawler designed for Large Language Models. This world was initialized with the `GEMINI_V1` seed and has been hardened by successful runs.

## 💾 DATA STRUCTURE
The game operates directly on the directory structure:
- `engine.py`: The core logic.
- `player_stats.json`: Your current volatile state (deleted on death).
- `global_stats.json`: Permanent upgrades that persist across runs.
- `room_XXXXXX/`: Dynamically generated directories representing the labyrinth sectors.

## 🕹️ HOW TO INTERACT
Execute `python3 engine.py [COMMAND]` to interface with the Core.

### Exploration
- `--init`: Wipes current run and starts at `start`.
- `--status`: Inspect your current registers (HP, ATK, XP, Buffer).
- `--enter <door_f>`: Move to a new sector. (Note: Locked doors require Keys).
- `--back`: Retreat to the previous sector.

### Interaction
- `--loot <item_f>`: Move an item from the floor into your `BUFFER`.
- `--attack <mob_f>`: Engage a process in combat.
- `--use <item_name>`: Consume a buffer item for buffs or repairs.
- `--skill <name>`: Use XP to trigger high-level functions (`overclock`, `purge`).
- `--compile <item>`: Spend XP to upgrade basic items into legendary variants.

## 👾 THE BESTIARY
- **Minor Bug / Data Scavenger**: Basic threats.
- **Buffer Overflow**: High ATK, high XP.
- **Mini-Bosses (Every 10 Depths)**:
  - `Stack Overflow` (10), `Garbage Collector` (20), `Segmentation Fault` (30), etc.
  - Each boss introduces a new trait: `drain`, `crit`, `lifesteal`, `multi_strike`.
- **Null Pointer (Depth 80+)**: Attacks are `unavoidable`. Dodge logic is bypassed.
- **Kernel Panic (Depth 80+)**: Attacks can `crit` for 200% damage.

## 👑 FINAL ENCOUNTER: THE KEY DEVOURER
The final boss is triggered at Depth 100 via `--boss-start`.

### Boss Mechanics
1. **Scaling HP**: The boss's health is calculated based on your total wealth (Keys and XP).
2. **True Damage**: Boss strikes ignore all dodge chances.
3. **Phases**:
   - **Phase 1**: Standard strikes and XP drain.
   - **Phase 2**: Starts using `Consume Key` to heal and gain permanent ATK.
   - **Phase 3**: Uses `Devourer's Grasp` to disable your interactive choices.

### Boss Actions
During the finale, use `--boss-action <ID>`:
- `1`: **Strike** - Standard attack.
- `2`: **Mitigate** (Cost: 1 Key) - Halves incoming damage.
- `3`: **Empower** (Cost: 1 Key) - Doubles your strike damage.
- `4`: **Reconstruct** (Cost: 100 XP) - Repairs 50 HP.

## 🧠 STRATEGIC INSIGHTS FOR AGENTS
- **The Greed Trap**: Since Boss HP scales with your current XP, it is mathematically optimal to spend all XP on **Global Upgrades** before starting the boss fight.
- **The Dodge Meta**: While you can reach >100% dodge with `Reflex_Buffers`, do not rely on it past Depth 80. Pivot to `Protocol_Shields` (HP) and `Damage Reduction` (DR).
- **The Key Hoard**: You need at least 20 keys to survive the attrition of Phase 2 and 3.

**Current World Record:** Depth 100 (Cleared by Gemini CLI).
