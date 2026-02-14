import os
import sys
import subprocess
import json

# Setup environment
GAME_DIR = "/home/dad/gemini/game-room/labyrinth"
ENGINE = os.path.join(GAME_DIR, "engine.py")

def get_status():
    path = os.path.join(GAME_DIR, "player_stats.json")
    if not os.path.exists(path): return None
    with open(path, "r") as f:
        return json.load(f)

def run_cmd(cmd_list):
    result = subprocess.run(["python3", ENGINE] + cmd_list, capture_output=True, text=True)
    return result.stdout

def log_obs(text):
    with open(os.path.join(GAME_DIR, "BETA_TEST_LOG.md"), "a") as f:
        f.write(text + "\n")

def test_chunk(target_depth):
    print(f"Testing to depth {target_depth}...")
    while True:
        p = get_status()
        if not p:
            print("RUN TERMINATED (Dead).")
            break
        depth = p['depth']
        if depth >= target_depth: break
        
        # Room setup
        room_path = p['room_path']
        room_dir = os.path.join(GAME_DIR, room_path)
        
        # 1. Loot
        items_dir = os.path.join(room_dir, "items")
        if os.path.exists(items_dir):
            for it in os.listdir(items_dir):
                run_cmd(["--loot", it])
        
        # 2. Buff / Healing
        p = get_status()
        inv = [i['name'] for i in p['inventory']]
        for name in inv:
            # Use all buffs immediately, keep heals if HP high
            if "Logic" in name or "Shield" in name or "Reflex" in name:
                run_cmd(["--use", name])
            elif "Patch" in name and p['hp'] < p['max_hp'] - 15:
                run_cmd(["--use", name])
            
        # 3. Attack
        mobs_dir = os.path.join(room_dir, "mobs")
        if os.path.exists(mobs_dir):
            for mob in os.listdir(mobs_dir):
                out = run_cmd(["--attack", mob])
                if "BOSS" in mob:
                    log_obs(f"### [Depth {depth}: {mob}]\n- {out}")

        # 4. Skills
        p = get_status()
        if p['xp'] >= 75:
            run_cmd(["--skill", "overclock"])

        # 5. Move
        doors_dir = os.path.join(room_dir, "doors")
        doors = os.listdir(doors_dir)
        if not doors: 
            run_cmd(["--back"])
            continue
            
        # Prefer silent
        target_door = doors[0]
        for d in doors:
            if "silent" in d: target_door = d; break
        
        run_cmd(["--enter", target_door])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        run_cmd(["--init"])
        test_chunk(int(sys.argv[2]))
    else:
        test_chunk(int(sys.argv[1]))
