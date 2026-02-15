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
    # print(f"Executing: {' '.join(cmd)}")
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
            print(f"{Colors.GREEN}Looting {item_f}...{Colors.END}")
            run_engine("--loot", item_f)

def auto_manage_inventory():
    p = get_player()
    if not p: return
    
    # Use all buffs and keys immediately
    for item in list(p['inventory']):
        if item['type'] == "buff":
            print(f"{Colors.YELLOW}Using buff: {item['name']}{Colors.END}")
            run_engine("--use", item['name'])
        elif item['type'] == "key":
            print(f"{Colors.CYAN}Consuming Sector Key item...{Colors.END}")
            run_engine("--use", item['name'])
    
    # Refresh player state
    p = get_player()
    
    # Dynamic Healing Threshold
    threshold = 0.9 if p['depth'] >= 80 else 0.7
    
    if p['hp'] < p['max_hp'] * threshold:
        for item in list(p['inventory']):
            if item['type'] == "heal":
                print(f"{Colors.GREEN}HP CRITICAL ({p['hp']}/{p['max_hp']}). Healing with {item['name']}...{Colors.END}")
                run_engine("--use", item['name'])
                p = get_player() # Update state after heal
                if p['hp'] >= p['max_hp'] * threshold: break

def fight_mobs(player):
    room_path = os.path.join(GAME_DIR, player['room_path'])
    mobs_dir = os.path.join(room_path, "mobs")
    if not os.path.exists(mobs_dir): return

    for mob_f in os.listdir(mobs_dir):
        print(f"{Colors.RED}Engaging {mob_f}...{Colors.END}")
        run_engine("--attack", mob_f)
        
        while os.path.exists(COMBAT_FILE):
            c = get_combat()
            if not c or not c['active']: break
            
            p = get_player()
            
            # Special logic for Key Devourer
            if "Key Devourer" in c['mob_name']:
                # Stun lock logic
                lock_turns = c.get('lock_turns', 0)
                if lock_turns <= 1 and p['keys'] > 0:
                    run_engine("--op", "LOCK")
                elif c['mob_hp'] < (c['mob_max_hp'] * 0.25):
                    run_engine("--purge-cmd")
                else:
                    run_engine("--op", "MOV")
            else:
                # Normal mob logic
                # Only purge if we are high depth and mob is scary, 
                # but purge costs ALL XP, so usually better to just MOV.
                run_engine("--op", "MOV")
            
            time.sleep(0.1)

def main():
    print(f"{Colors.BOLD}{Colors.PURPLE}Initializing Ascent...{Colors.END}")
    run_engine("--init")
    
    while True:
        p = get_player()
        if not p:
            print(f"{Colors.RED}Player state lost. Termination detected.{Colors.END}")
            break
            
        print(f"\n{Colors.BOLD}{Colors.CYAN}[DEPTH {p['depth']}]{Colors.END} Current Sector: {p['room_path']} | HP: {p['hp']}/{p['max_hp']} | Keys: {p['keys']}")
        
        # 1. Loot
        auto_loot(p)
        
        # 2. Manage Inventory
        auto_manage_inventory()
        
        # 3. Fight
        fight_mobs(p)
        
        # 4. Refresh stats after fight
        p = get_player()
        if not p: break
        
        # 5. Check if we reached the end
        if p['depth'] >= 100:
            print(f"{Colors.BOLD}{Colors.PURPLE}REACHED DEPTH 100. FINAL BOSS SHOULD BE PURGED.{Colors.END}")
            break
            
        # 6. Defrag if needed
        if p['fragmentation'] > 100:
            run_engine("--defrag")
            
        # 7. Advance
        room_path = os.path.join(GAME_DIR, p['room_path'])
        doors_dir = os.path.join(room_path, "doors")
        if os.path.exists(doors_dir):
            doors = os.listdir(doors_dir)
            if doors:
                # Prefer ROOT or FIREWALL if possible
                target_door = doors[0]
                for d in doors:
                    if "root" in d.lower(): target_door = d; break
                
                print(f"Entering door: {Colors.BOLD}{target_door}{Colors.END}")
                run_engine("--enter", target_door)
            else:
                print(f"{Colors.RED}No doors found! Dead end?{Colors.END}")
                break
        else:
            print(f"{Colors.RED}Doors directory missing!{Colors.END}")
            break
            
        time.sleep(0.1)

if __name__ == "__main__":
    main()
