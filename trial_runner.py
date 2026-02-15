import os
import subprocess
import json
import time

GAME_DIR = "/home/dad/gemini/game-room/labyrinth"
ENGINE = os.path.join(GAME_DIR, "engine.py")
PLAYER_FILE = os.path.join(GAME_DIR, "player_stats.json")
COMBAT_FILE = os.path.join(GAME_DIR, "combat_state.json")

def reset_player():
    stats = {
        "hp": 683, "max_hp": 1605, "atk": 209, "crit": 32, "dodge": 35, "dr": 17,
        "percent_dmg": 0, "xp": 2665, "lvl": 11, "xp_to_lvl": 11524,
        "shield_turns": 0, "room_path": "room_2476c9", "depth": 100,
        "inventory": [], "corruption": 0, "backlog": [], "keys": 23,
        "path_history": [], "overclocked": False, "battles_won": 57,
        "class": "SysAdmin (Tank)", "mem_capacity": 256, "mem_used": 0,
        "fragmentation": 56, "symlinks": []
    }
    with open(PLAYER_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def get_combat_state():
    if os.path.exists(COMBAT_FILE):
        with open(COMBAT_FILE, "r") as f:
            return json.load(f)
    return None

def run_cmd(args):
    return subprocess.run(["python3", ENGINE] + args, capture_output=True, text=True, cwd=GAME_DIR)

def run_trial(trial_num):
    print(f"--- Trial {trial_num} ---")
    reset_player()
    if os.path.exists(COMBAT_FILE):
        os.remove(COMBAT_FILE)
    
    # Init combat
    run_cmd(["--attack", "BOSS_[BOSS]_Key_Devourer.json"])
    
    turn = 1
    while True:
        c = get_combat_state()
        if not c:
            print(f"Trial {trial_num} failed: Combat ended (Player likely died).")
            return False
        
        # Check if we can purge
        if c['mob_hp'] < (c['mob_max_hp'] * 0.25):
            print(f"Boss HP at {c['mob_hp']}/{c['mob_max_hp']}. Attempting PURGE!")
            res = run_cmd(["--purge-cmd"])
            print(res.stdout)
            if "CONQUERED" in res.stdout:
                return True
            return False

        # Strategy: Keep LOCK active
        if c.get('lock_turns', 0) <= 1:
            res = run_cmd(["--op", "LOCK"])
        else:
            res = run_cmd(["--op", "MOV"])
        
        # Print all lines of output
        for line in res.stdout.splitlines():
            if line.strip():
                print(f"T{turn}: {line}")
        
        if "RUN TERMINATED" in res.stdout:
            print(f"Trial {trial_num} failed: Player died.")
            return False
        
        turn += 1
        if turn > 50: # Failsafe
            return False

results = []
for i in range(1, 11):
    success = run_trial(i)
    results.append(success)
    if success:
        print(f"SUCCESS ON TRIAL {i}!")
    time.sleep(0.5)

print("\n=== FINAL RESULTS ===")
print(f"Successes: {sum(results)}/10")
