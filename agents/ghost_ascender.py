import os
import json
import subprocess
import time
import sys

GAME_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_FILE = os.path.join(GAME_DIR, "player_stats.json")
COMBAT_FILE = os.path.join(GAME_DIR, "combat_state.json")

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def run_engine(*args):
    cmd = ["python3", "engine.py"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(f"{Colors.RED}ERR: {result.stderr.strip()}{Colors.END}")
    return result.stdout

def get_player():
    if not os.path.exists(PLAYER_FILE): return None
    with open(PLAYER_FILE, "r") as f: return json.load(f)

def get_combat():
    if not os.path.exists(COMBAT_FILE): return None
    with open(COMBAT_FILE, "r") as f: return json.load(f)

def auto_loot(player):
    room_path = os.path.join(GAME_DIR, player['room_path'])
    items_dir = os.path.join(room_path, "items")
    if os.path.exists(items_dir):
        for item_f in os.listdir(items_dir):
            print(f"{Colors.GREEN}Ghosting item: {item_f}...{Colors.END}")
            run_engine("--loot", item_f)

def auto_manage_inventory():
    p = get_player()
    if not p: return
    # The Ghost uses ALL defensive/agility buffs EXCEPT those that reduce dodge
    for item in list(p['inventory']):
        if item['type'] in ["buff", "key"]:
            if item.get('dodge', 0) < 0:
                print(f"{Colors.YELLOW}Ghosting: Skipping heavy item {item['name']} to maintain agility.{Colors.END}")
                continue
            print(f"{Colors.CYAN}Syncing: {item['name']}{Colors.END}")
            run_engine("--use", item['name'])
    
    p = get_player()
    # Ghost heals very early to keep a "High Health Buffer"
    if p['hp'] < p['max_hp'] * 0.8:
        for item in list(p['inventory']):
            if item['type'] == "heal":
                print(f"{Colors.GREEN}Restoring Core Integrity...{Colors.END}")
                run_engine("--use", item['name'])
                break

def fight_mobs(player):
    room_path = os.path.join(GAME_DIR, player['room_path'])
    mobs_dir = os.path.join(room_path, "mobs")
    if not os.path.exists(mobs_dir): return

    for mob_f in os.listdir(mobs_dir):
        print(f"{Colors.BOLD}{Colors.PURPLE}>> ENEMY DETECTED: {mob_f}{Colors.END}")
        run_engine("--attack", mob_f)
        
        turn_count = 0
        while os.path.exists(COMBAT_FILE):
            c = get_combat()
            if not c or not c['active']: break
            p = get_player()
            
            # GHOST LOGIC: XOR (Encryption) -> LOCK (Stun) -> MOV (Strike)
            if "Key Devourer" in c['mob_name']:
                lock_turns = c.get('lock_turns', 0)
                if lock_turns == 0 and p['keys'] > 0:
                    run_engine("--op", "LOCK")
                elif c['mob_hp'] < (c['mob_max_hp'] * 0.25):
                    run_engine("--purge-cmd")
                elif turn_count % 4 == 0: # Periodically XOR for extra safety
                    run_engine("--op", "XOR")
                else:
                    run_engine("--op", "MOV")
            else:
                # Normal combat: XOR first to reflect damage, then MOV
                if turn_count == 0:
                    run_engine("--op", "XOR")
                else:
                    run_engine("--op", "MOV")
            
            turn_count += 1
            time.sleep(0.05)

def main():
    print(f"{Colors.BOLD}{Colors.PURPLE}--- GHOST PROTOCOL ACTIVATED ---{Colors.END}")
    run_engine("--init")
    
    while True:
        p = get_player()
        if not p: break
            
        print(f"\n{Colors.CYAN}[DEPTH {p['depth']}]{Colors.END} HP: {p['hp']} | DODGE: {p['dodge']}% | DR: {p['dr']}")
        auto_loot(p)
        auto_manage_inventory()
        fight_mobs(p)
        
        p = get_player()
        if not p: break
        if p['depth'] >= 100: break
        if p['fragmentation'] > 150: run_engine("--defrag")
            
        room_path = os.path.join(GAME_DIR, p['room_path'])
        doors_dir = os.path.join(room_path, "doors")
        if os.path.exists(doors_dir):
            doors = os.listdir(doors_dir)
            if doors:
                # GHOST PREFERENCE: EXPLOIT (Dodge) > FIREWALL (DR/Heal) > ROOT
                # If HP is low, prioritize FIREWALL to find Cache Patches
                target_door = doors[0]
                if p['hp'] < p['max_hp'] * 0.5:
                    pref = ["firewall", "exploit", "root"]
                    print(f"{Colors.YELLOW}>> INTEGRITY COMPROMISED: Seeking Firewall for repairs...{Colors.END}")
                else:
                    pref = ["exploit", "firewall", "root"]
                
                found = False
                for p_type in pref:
                    for d in doors:
                        if p_type in d.lower(): 
                            target_door = d; found = True; break
                    if found: break
                
                print(f"Slipping through: {Colors.BOLD}{target_door}{Colors.END}")
                run_engine("--enter", target_door)
            else: break
        else: break
        time.sleep(0.05)

if __name__ == "__main__":
    main()
