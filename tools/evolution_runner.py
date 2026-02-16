import os
import subprocess
import json
import time

GAME_DIR = "/home/dad/gemini/game-room/labyrinth"
ENGINE = os.path.join(GAME_DIR, "engine.py")
GLOBAL_FILE = os.path.join(GAME_DIR, "global_stats.json")
LOG_FILE = "evolution_log.txt"

def get_global_xp():
    with open(GLOBAL_FILE, "r") as f:
        return json.load(f)['total_xp']

def run_ascender():
    print(">> Starting run with sysadmin_ascender.py...")
    result = subprocess.run(["python3", "sysadmin_ascender.py"], capture_output=True, text=True, cwd=GAME_DIR)
    
    depth = 0
    conquered = False
    for line in result.stdout.splitlines():
        if "[DEPTH" in line:
            try:
                depth = int(line.split("[DEPTH ")[1].split("]")[0])
            except: pass
        if "CONQUERED" in line:
            conquered = True
    
    return depth, conquered

def buy_upgrades():
    xp = get_global_xp()
    print(f">> Available Global XP: {xp}")
    upgrades = 0
    while xp >= 200:
        if upgrades % 5 < 3: stat = "hp"
        elif upgrades % 5 < 4: stat = "atk"
        else: stat = "dodge"
            
        subprocess.run(["python3", ENGINE, "--upgrade", stat], capture_output=True, cwd=GAME_DIR)
        xp -= 200
        upgrades += 1
    print(f">> Purchased {upgrades} upgrades.")

def main():
    if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
    attempts = 0
    total_conquered = False
    
    with open(LOG_FILE, "a") as log:
        log.write("--- EVOLUTION RUN START ---\n")
        while not total_conquered:
            attempts += 1
            depth, conquered = run_ascender()
            xp_after = get_global_xp()
            status = f"Attempt {attempts}: Reached Depth {depth} | Conquered: {conquered} | Global XP: {xp_after}"
            print(status)
            log.write(status + "\n")
            if conquered:
                total_conquered = True
                print(f"!!! LABYRINTH CONQUERED IN {attempts} ATTEMPTS !!!")
                log.write(f"!!! LABYRINTH CONQUERED IN {attempts} ATTEMPTS !!!\n")
            else:
                buy_upgrades()
            if attempts > 200: break

if __name__ == "__main__":
    main()
