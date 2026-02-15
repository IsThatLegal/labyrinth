import os
import sys
import random
import json
import hashlib
import time
import copy

# Colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Configuration
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_FILE = os.path.join(GAME_DIR, "player_stats.json")
GLOBAL_FILE = os.path.join(GAME_DIR, "global_stats.json")
LOG_FILE = os.path.join(GAME_DIR, "session_log.json")
BOSS_FILE = os.path.join(GAME_DIR, "boss_state.json")
COMBAT_FILE = os.path.join(GAME_DIR, "combat_state.json")
WORLD_SEED = "GEMINI_V1"

# Content Mapping
MOBS = {
    0x01: {"name": "Minor Bug", "hp": 10, "atk": 2, "xp": 10},
    0x02: {"name": "Data Scavenger", "hp": 15, "atk": 3, "xp": 20},
    0x03: {"name": "Buffer Overflow", "hp": 25, "atk": 5, "xp": 50},
}
SPECIAL_MOBS = {
    0x04: {"name": "Null Pointer", "hp": 40, "atk": 10, "xp": 100, "traits": ["true_dmg"]},
    0x05: {"name": "Kernel Panic", "hp": 50, "atk": 12, "xp": 120, "traits": ["crit"]},
    0x10: {"name": "[BOSS] Stack Overflow", "hp": 100, "atk": 8, "xp": 250},
    0x20: {"name": "[BOSS] Garbage Collector", "hp": 150, "atk": 12, "xp": 400, "traits": ["drain"]},
    0x30: {"name": "[BOSS] Segmentation Fault", "hp": 200, "atk": 15, "xp": 600, "traits": ["crit"]},
    0x40: {"name": "[BOSS] Logic Bomb", "hp": 100, "atk": 30, "xp": 800},
    0x50: {"name": "[BOSS] Purge Sentinel", "hp": 300, "atk": 25, "xp": 1000},
    0x60: {"name": "[BOSS] Memory Leak", "hp": 350, "atk": 30, "xp": 1200, "traits": ["lifesteal"]},
    0x70: {"name": "[BOSS] Race Condition", "hp": 400, "atk": 45, "xp": 1500, "traits": ["multi_strike", "race_condition"]},
    0x80: {"name": "[BOSS] Null Pointer Overlord", "hp": 500, "atk": 50, "xp": 2000, "traits": ["true_dmg"]},
    0x90: {"name": "[BOSS] Kernel Panic Archon", "hp": 600, "atk": 60, "xp": 3000, "traits": ["crit", "true_dmg"]},
    0xA0: {"name": "[BOSS] Key Devourer", "hp": 2000, "atk": 150, "xp": 10000, "traits": ["true_dmg", "drain", "race_condition"]},
}
ITEMS = {
    0x20: {"name": "Cache_Patch", "type": "heal", "value": 15, "size": 16, "desc": "Restores 15 HP"},
    0x23: {"name": "Sector_Key", "type": "key", "size": 8, "desc": "Unlocks encrypted doors."},
    0x30: {"name": "Logic_Blade", "type": "buff", "stat": "atk", "value": 3, "size": 32, "desc": "+3 ATK (Root)"},
    0x31: {"name": "Compiler_Loop", "type": "buff", "stat": "xp", "value": 50, "size": 24, "desc": "+50 Instant XP (Root)"},
    0x32: {"name": "Syntax_Lens", "type": "buff", "stat": "crit", "value": 2, "size": 16, "desc": "+2% Crit (Root)"},
    0x40: {"name": "Protocol_Shield", "type": "buff", "stat": "max_hp", "value": 15, "dr": 1, "size": 48, "desc": "+15 Max HP & 1 DR (Firewall)"},
    0x41: {"name": "Heavy_Kernel", "type": "buff", "stat": "max_hp", "value": 30, "size": 64, "desc": "+30 Max HP (Firewall)"},
    0x42: {"name": "Iron_Clad_Mesh", "type": "buff", "stat": "dr", "value": 2, "size": 80, "desc": "+2 DR (Firewall)"},
    0x50: {"name": "Reflex_Buffer", "type": "buff", "stat": "dodge", "value": 5, "size": 24, "desc": "+5% Dodge (Exploit)"},
    0x51: {"name": "Zero_Day_Shiv", "type": "buff", "stat": "crit", "value": 5, "size": 32, "desc": "+5% Crit (Exploit)"},
    0x52: {"name": "Ghost_Protocol", "type": "buff", "stat": "dodge", "value": 3, "atk": 1, "size": 40, "desc": "+3% Dodge & +1 ATK (Exploit)"},
}
DOOR_TYPES = {
    "ROOT": {"desc": "A pulsing data stream promising POWER.", "loot_table": [0x30, 0x31, 0x32]},
    "FIREWALL": {"desc": "A heavily reinforced blast door promising DEFENSE.", "loot_table": [0x40, 0x41, 0x42]},
    "EXPLOIT": {"desc": "A glitching, unstable rift promising AGILITY.", "loot_table": [0x50, 0x51, 0x52]},
}
RARITIES = {
    "COMMON": {"chance": 0.70, "stat_mult": 1.0, "xp_mult": 1, "color": ""},
    "RARE": {"chance": 0.20, "stat_mult": 1.5, "xp_mult": 2, "color": f"{Colors.CYAN}[RARE]{Colors.END} "},
    "ELITE": {"chance": 0.08, "stat_mult": 2.5, "xp_mult": 5, "color": f"{Colors.YELLOW}[ELITE]{Colors.END} "},
    "LEGENDARY": {"chance": 0.02, "stat_mult": 5.0, "xp_mult": 20, "color": f"{Colors.PURPLE}{Colors.BOLD}[LEGENDARY]{Colors.END} "},
}

class DelveEngine:
    def __init__(self, seed=WORLD_SEED):
        self.seed = seed
        self.globals = self.load_global()
        self.player = self.load_player()
        self.session = self.load_session()

    def load_global(self):
        if os.path.exists(GLOBAL_FILE):
            with open(GLOBAL_FILE, "r") as f: return json.load(f)
        return {"total_xp": 0, "base_hp": 50, "base_atk": 5, "base_crit": 10, "base_dodge": 15}

    def save_global(self):
        with open(GLOBAL_FILE, "w") as f: json.dump(self.globals, f, indent=4)

    def load_player(self):
        if os.path.exists(PLAYER_FILE):
            with open(PLAYER_FILE, "r") as f:
                p = json.load(f)
                p.setdefault("dr", 0); p.setdefault("percent_dmg", 0); p.setdefault("shield_turns", 0)
                p.setdefault("lvl", 1); p.setdefault("xp_to_lvl", 200); p.setdefault("path_history", [])
                p.setdefault("class", "Novice"); p.setdefault("mem_capacity", 256); p.setdefault("mem_used", 0)
                p.setdefault("fragmentation", 0); p.setdefault("symlinks", [])
                return p
        return self.reset_run()

    def reset_run(self):
        new_p = {
            "hp": self.globals['base_hp'], "max_hp": self.globals['base_hp'],
            "atk": self.globals['base_atk'], "crit": self.globals['base_crit'],
            "dodge": self.globals['base_dodge'], "dr": 0, "percent_dmg": 0,
            "xp": 0, "lvl": 1, "xp_to_lvl": 200, "shield_turns": 0,
            "room_path": "start", "depth": 0, "inventory": [], "corruption": 0,
            "backlog": [], "keys": 0, "path_history": [], "overclocked": False, "battles_won": 0,
            "class": "Novice", "mem_capacity": 256, "mem_used": 0, "fragmentation": 0, "symlinks": []
        }
        self.save_player(new_p)
        return new_p

    def save_player(self, data):
        with open(PLAYER_FILE, "w") as f: json.dump(data, f, indent=4)

    def load_session(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: return json.load(f)
        return {"start_time": time.time(), "events": []}

    def save_session(self):
        with open(LOG_FILE, "w") as f: json.dump(self.session, f, indent=4)

    def check_level_up(self):
        while self.player['xp'] >= self.player['xp_to_lvl']:
            self.player['xp'] -= self.player['xp_to_lvl']
            self.player['lvl'] += 1
            self.player['xp_to_lvl'] = int(self.player['xp_to_lvl'] * 1.5)
            self.player['atk'] += 3; self.player['max_hp'] += 20; self.player['hp'] += 20
            self.player['dodge'] = min(75, self.player['dodge'] + 2)
            p = self.player
            if p['dr'] >= 5 or p['max_hp'] > 200: p['class'] = "SysAdmin (Tank)"
            elif p['dodge'] > 40 or p['crit'] > 25: p['class'] = "Ghost (Rogue)"
            elif p['atk'] > 40: p['class'] = "Netrunner (DPS)"
            print(f"KERNEL UPGRADED TO LVL {self.player['lvl']}! Class: {p['class']}")

    def get_rarity(self, rng):
        roll = rng.random(); cumulative = 0; depth = self.player['depth']
        avail = ["COMMON"]
        if depth >= 10: avail.append("RARE")
        if depth >= 20: avail.append("ELITE")
        if depth >= 40: avail.append("LEGENDARY")
        for n in avail:
            cumulative += RARITIES[n]['chance']
            if roll <= cumulative: return n
        return "COMMON"

    def get_scaled_mob(self, mob_id, rng, forced_rarity=None, is_ghost=False):
        all_mobs = {**MOBS, **SPECIAL_MOBS}
        mob = copy.deepcopy(all_mobs[mob_id])
        rarity_name = forced_rarity if forced_rarity else self.get_rarity(rng)
        rarity = RARITIES[rarity_name]; depth = self.player['depth']
        d_mult = 1.0 + (depth // 5) * 0.1
        if mob_id in SPECIAL_MOBS and mob_id >= 0x10: d_mult = min(1.3, d_mult)
        c_mult = 1.0 + (self.player['corruption'] / 100.0) * 0.5 if depth >= 20 else 1.0
        if depth >= 20: d_mult += 0.2
        if depth >= 50: d_mult += 0.5
        g_mult = 1.2 if is_ghost else 1.0
        f_mult = d_mult * rarity['stat_mult'] * c_mult * g_mult
        mob['name'] = ("[GHOST] " if is_ghost else "") + rarity['color'] + mob['name']
        mob['hp'] = int(mob['hp'] * f_mult); mob['atk'] = int(mob['atk'] * f_mult)
        mob['xp'] = int(mob['xp'] * d_mult * rarity['xp_mult'])
        return mob

    def defrag(self):
        cost = 50
        if self.player['xp'] >= cost:
            self.player['xp'] -= cost
            self.player['fragmentation'] = 0
            print(">> DEFRAG COMPLETE: Memory address space consolidated."); self.save_player(self.player)
        else: print(f"Need {cost} XP to defrag.")

    def loot(self, item_filename):
        item_path = os.path.join(GAME_DIR, self.player['room_path'], "items", item_filename)
        if not os.path.exists(item_path): return
        with open(item_path, "r") as f: item = json.load(f)
        size = item.get('size', 16)
        if self.player['mem_used'] + self.player['fragmentation'] + size > self.player['mem_capacity']:
            print(f"[!] MALLOC FAILURE: Buffer too fragmented or full ({self.player['mem_used']}+{self.player['fragmentation']}+{size} > {self.player['mem_capacity']})")
            return
        print(f"Buffer + {item['name']} ({size} bytes)")
        self.player['inventory'].append(item); self.player['mem_used'] += size
        os.remove(item_path); self.save_player(self.player)

    def use_item(self, item_name):
        for i, it in enumerate(self.player['inventory']):
            if it['name'] == item_name:
                item = self.player['inventory'].pop(i)
                size = item.get('size', 16)
                self.player['mem_used'] -= size; self.player['fragmentation'] += size
                if item['type'] == "heal":
                    v = item['value']; self.player['hp'] = min(self.player['max_hp'], self.player['hp'] + v)
                    print(f"HP Restored. Hole created: {size} bytes.")
                elif item['type'] == "buff":
                    self.player[item['stat']] += item['value']
                    if 'dr' in item: self.player['dr'] += item['dr']
                    if item['stat'] == "max_hp": self.player['hp'] += item['value']
                    if item['stat'] == "xp": self.player['xp'] += item['value']
                    if 'atk' in item and item['stat'] != 'atk': self.player['atk'] += item['atk']
                    print(f"Applied {item['name']}. Hole created: {size} bytes.")
                elif item['type'] == "key": self.player['keys'] += 1
                self.save_player(self.player); return
        print("Item not found.")

    def attack_init(self, mob_filename):
        mob_path = os.path.join(GAME_DIR, self.player['room_path'], "mobs", mob_filename)
        if not os.path.exists(mob_path): return
        with open(mob_path, "r") as f: mob = json.load(f)
        state = {
            "mob_name": mob['name'], "mob_hp": mob['hp'], "mob_max_hp": mob['hp'],
            "mob_atk": mob['atk'], "mob_traits": mob.get('traits', []), "mob_xp": mob['xp'],
            "mob_filename": mob_filename, "multiplier": 1.0, "active": True
        }
        with open(COMBAT_FILE, "w") as f: json.dump(state, f, indent=4)
        print(f"--- I.P. COMBAT INITIALIZED: {mob['name']} ---")
        print("Queue Opcode: --op <MOV|NOP|ADD|XOR|LOCK>")

    def combat_turn(self, opcode):
        if not os.path.exists(COMBAT_FILE): print("No combat active."); return
        with open(COMBAT_FILE, "r") as f: c = json.load(f)
        p = self.player
        if not c['active']: return
        
        c.setdefault('lock_turns', 0)
        
        # Player Turn
        print(f">> IP: Executing {opcode}...")
        p_dmg = 0
        if opcode == "MOV":
            p_dmg = int(p['atk'] * c['multiplier'])
            if random.random() < (p['crit'] / 100.0): p_dmg *= 2; print(f"{Colors.RED}{Colors.BOLD}CRITICAL!{Colors.END}")
            c['mob_hp'] -= p_dmg; c['multiplier'] = 1.0
            print(f"Result: {Colors.GREEN}{p_dmg} DMG{Colors.END} to {c['mob_name']}.")
        elif opcode == "NOP":
            c['multiplier'] *= 2.0; print("Result: CPU Cycle skipped. Next MOV doubled.")
        elif opcode == "ADD":
            p['atk'] += 2; print(f"Result: {Colors.YELLOW}ATK permanently increased by 2{Colors.END} for this fight.")
        elif opcode == "XOR":
            p['dr'] += 10; print(f"Result: {Colors.CYAN}Temporary encryption active. +10 DR and Reflective Shell engaged.{Colors.END}")
        elif opcode == "LOCK":
            if p['keys'] > 0:
                p['keys'] -= 1; c['lock_turns'] = 3
                if "Key Devourer" in c['mob_name']:
                    c.setdefault('keys_fed', 0)
                    c['keys_fed'] += 1
                    print(f"{Colors.YELLOW}>> KEY FEED: The Devourer is occupied with your Sector Key! (System Frozen for 3 turns){Colors.END}")
                    c['mob_hp'] = min(c['mob_max_hp'], c['mob_hp'] + 100)
                    c['mob_atk'] += 5
                    print(f">> INCORPORATION: The boss consumed key #{c['keys_fed']}! {Colors.GREEN}+100 HP{Colors.END} and {Colors.YELLOW}+5 ATK{Colors.END}.")
                    
                    fb_dmg = 0
                    if c['keys_fed'] > 30:
                        print(f"\n{Colors.RED}{Colors.BOLD}!!! CRITICAL OVERLOAD: The Devourer has reached maximum capacity and EXPLODES !!!{Colors.END}")
                        print(">> The resulting data shockwave vaporizes your core connection.")
                        self.terminate()
                    elif c['keys_fed'] > 20:
                        print(f"{Colors.RED}>> DISGUST: The Devourer poops out a corrupted memory block. It looks dangerously bloated.{Colors.END}")
                        fb_dmg = 41
                    elif c['keys_fed'] > 15:
                        print(f"{Colors.YELLOW}>> REJECTION: The Devourer barfs uncompiled code! Its internal pressure is rising.{Colors.END}")
                        fb_dmg = 60
                    elif c['keys_fed'] > 8:
                        print(f"{Colors.CYAN}>> GASEOUS: A digital fart echoes through the sector. The air smells of ozone and burnt silicon.{Colors.END}")
                        fb_dmg = 30
                    else:
                        print(f"{Colors.GREEN}>> SATIATED: The Devourer lets out a data-heavy burp.{Colors.END}")
                        fb_dmg = 10
                    
                    if fb_dmg > 0:
                        if random.random() < (p['dodge'] / 100.0):
                            print(f"{Colors.CYAN}>> AVOIDED: You dodged the digital fallout!{Colors.END}")
                        else:
                            p['hp'] -= fb_dmg
                            print(f"{Colors.RED}>> FEEDBACK: You took {fb_dmg} damage from the boss's reaction! ({p['hp']}/{p['max_hp']} HP){Colors.END}")
                else:
                    print(f"{Colors.CYAN}>> KERNEL LOCK: Sector Key used to throttle enemy process. (ATK -50% for 3 turns){Colors.END}")
            else:
                print(f"{Colors.RED}>> NO KEYS left to lock with!{Colors.END}")
        
        if c['mob_hp'] <= 0:
            print(f"{Colors.PURPLE}{Colors.BOLD}Purged! +{c['mob_xp']} XP{Colors.END}"); p['xp'] += c['mob_xp']; p['battles_won'] += 1; self.check_level_up()
            if p['depth'] >= 100:
                print("\n" + "="*40)
                print(f"{Colors.PURPLE}{Colors.BOLD}>> CORE BREACH SUCCESSFUL: THE LABYRINTH IS CONQUERED <<{Colors.END}")
                print("="*40 + "\n")
                self.globals['total_xp'] += p['xp']; self.save_global()
                if os.path.exists(PLAYER_FILE): os.remove(PLAYER_FILE)
                sys.exit()
            if random.random() < 0.25:
                p['keys'] += 1; print(f"{Colors.GREEN}>> DATA LEAK: Found 1 Sector Key in the wreckage.{Colors.END}")
            os.remove(os.path.join(GAME_DIR, p['room_path'], "mobs", c['mob_filename']))
            os.remove(COMBAT_FILE); self.save_player(p); return

        # Mob Turn
        hit = True
        is_stunned = c.get('lock_turns', 0) > 0 and "Key Devourer" in c['mob_name']
        
        if is_stunned:
            print(f"{Colors.CYAN}>> STUNNED: Key Devourer is busy eating! ({c['lock_turns']} turns left){Colors.END}")
            c['lock_turns'] -= 1
            hit = False
        elif "true_dmg" not in c['mob_traits']:
            if random.random() < (p['dodge'] / 100.0): print(f"{Colors.CYAN}EVADED!{Colors.END}"); hit = False
        else: print(f"{Colors.RED}UNAVOIDABLE!{Colors.END}")
        
        if hit:
            dmg = max(1, c['mob_atk'] - p['dr'])
            if c.get('lock_turns', 0) > 0:
                dmg //= 2; c['lock_turns'] -= 1; print(f"{Colors.CYAN}>> THROTTLED: Kernel Lock active ({c['lock_turns']} turns left){Colors.END}")
            
            if "crit" in c['mob_traits'] and random.random() < 0.25:
                dmg *= 2; print(f"{Colors.RED}{Colors.BOLD}ENEMY CRIT!{Colors.END}")
            # Race Condition Check
            if "race_condition" in c['mob_traits'] and random.random() < 0.3:
                print(f"{Colors.RED}>> RACE CONDITION: Mob injected code into your pipeline!{Colors.END}"); p['hp'] -= p_dmg
                print(f"You struck yourself for {Colors.RED}{p_dmg} DMG!{Colors.END}")
            
            p['hp'] -= dmg; print(f"Took {Colors.RED}{dmg} DMG{Colors.END} ({p['hp']}/{p['max_hp']} HP)")
            if opcode == "XOR":
                reflect = dmg // 2; c['mob_hp'] -= reflect; p['dr'] -= 10
                print(f"{Colors.GREEN}>> REFLECTED: {reflect} DMG returned to {c['mob_name']}.{Colors.END}")

        if p['hp'] <= 0: self.terminate()
        with open(COMBAT_FILE, "w") as f: json.dump(c, f, indent=4)
        self.save_player(p)

    def symlink(self):
        if self.player['xp'] < 200: print("Need 200 XP for Symlink."); return
        self.player['xp'] -= 200
        link_id = f"link_{int(time.time())}"
        safe_path = os.path.join(GAME_DIR, "start", link_id)
        current_path = os.path.join(GAME_DIR, self.player['room_path'])
        os.symlink(current_path, safe_path)
        self.player['symlinks'].append({"id": link_id, "source": self.player['room_path']})
        print(f">> SYMLINK CREATED: {link_id} -> {self.player['room_path']}")
        self.save_player(self.player)

    def generate_room(self, path, door_type="ROOT", is_backtrack=False):
        room_seed = hashlib.sha256((self.seed + path).encode()).hexdigest()
        rng = random.Random(room_seed); depth = self.player['depth']
        room_dir = os.path.join(GAME_DIR, path); os.makedirs(room_dir, exist_ok=True)
        with open(os.path.join(room_dir, "room_info.txt"), "w") as f:
            f.write(f"--- SECTOR {path.upper()} ---\n")
            if is_backtrack: f.write("RE-ENTRY DETECTED.\n")
            f.write(f"DEPTH: {depth} | LVL: {self.player['lvl']} | CLASS: {self.player['class']}\n")
            f.write(DOOR_TYPES[door_type]["desc"] + "\nStatus: Awaiting input...\n")
        mobs_dir = os.path.join(room_dir, "mobs"); os.makedirs(mobs_dir, exist_ok=True)
        for f_n in os.listdir(mobs_dir): os.remove(os.path.join(mobs_dir, f_n))
        
        # Mobs can follow symlinks!
        if path == "start":
            for link in self.player['symlinks']:
                if random.random() < 0.3:
                    print(f"[!] WARNING: Signal leakage detected from {link['id']}!")
                    mob = self.get_scaled_mob(0x01, rng); mob['name'] = f"[LEAK] {mob['name']}"
                    with open(os.path.join(mobs_dir, f"LEAK_{mob['name']}.json"), "w") as f: json.dump(mob, f, indent=4)

        if depth > 0 and depth <= 100 and depth % 10 == 0:
            boss_id = 0x10 * (depth // 10)
            if boss_id in SPECIAL_MOBS:
                mob = self.get_scaled_mob(boss_id, rng, forced_rarity="COMMON")
                with open(os.path.join(mobs_dir, f"BOSS_{mob['name'].replace(' ', '_')}.json"), "w") as f: json.dump(mob, f, indent=4)
        elif rng.random() > 0.4:
            available_mobs = list(MOBS.keys())
            if depth >= 80: available_mobs.extend([0x04, 0x05])
            mob = self.get_scaled_mob(rng.choice(available_mobs), rng, is_ghost=(is_backtrack and rng.random() < 0.5))
            with open(os.path.join(mobs_dir, f"{mob['name'].replace(' ', '_')}.json"), "w") as f: json.dump(mob, f, indent=4)
        
        items_dir = os.path.join(room_dir, "items"); os.makedirs(items_dir, exist_ok=True)
        for f_n in os.listdir(items_dir): os.remove(os.path.join(items_dir, f_n))
        loot_table = DOOR_TYPES[door_type].get("loot_table", [0x20, 0x23])
        if depth % 10 == 9:
            it = ITEMS[0x40] # Protocol Shield
            with open(os.path.join(items_dir, f"{it['name']}.json"), "w") as f: json.dump(it, f, indent=4)
            it_key = ITEMS[0x23] # Sector Key
            with open(os.path.join(items_dir, f"{it_key['name']}.json"), "w") as f: json.dump(it_key, f, indent=4)
        elif rng.random() < 0.5:
            item_id = rng.choice(loot_table) if rng.random() < 0.8 else rng.choice([0x20, 0x23])
            it = ITEMS[item_id]
            with open(os.path.join(items_dir, f"{it['name']}.json"), "w") as f: json.dump(it, f, indent=4)
        
        doors_dir = os.path.join(room_dir, "doors"); os.makedirs(doors_dir, exist_ok=True)
        for f_n in os.listdir(doors_dir): os.remove(os.path.join(doors_dir, f_n))
        for i in range(rng.randint(1, 3)):
            dt = rng.choice(list(DOOR_TYPES.keys()))
            with open(os.path.join(doors_dir, f"door_{i}_{dt.lower()}.gate"), "w") as f:
                f.write(f"leads_to: {dt}\n")
                if depth > 0 and depth % 10 == 0: f.write("LOCKED: True")

    def enter_room(self, door_f):
        door_path = os.path.join(GAME_DIR, self.player['room_path'], "doors", door_f)
        print(f"DEBUG: Checking {door_path}")
        mobs_dir = os.path.join(GAME_DIR, self.player['room_path'], "mobs")
        active = os.listdir(mobs_dir) if os.path.exists(mobs_dir) else []
        door_path = os.path.join(GAME_DIR, self.player['room_path'], "doors", door_f)
        if os.path.exists(door_path):
            with open(door_path, "r") as f: d_data = f.read()
            if "LOCKED: True" in d_data:
                if self.player['keys'] > 0: self.player['keys'] -= 1; print("Unlocked.")
                else: print("LOCKED."); sys.exit(1)
        if active:
            if random.random() < 0.4:
                with open(os.path.join(mobs_dir, active[0]), "r") as f: mob = json.load(f)
                self.player['hp'] -= mob['atk']; print(f"Intercepted by {mob['name']}! Took {mob['atk']} DMG.")
                if self.player['hp'] <= 0: self.terminate()
        if not os.path.exists(door_path): return
        with open(door_path, "r") as f: dt = f.readlines()[0].split(": ")[1].strip()
        self.player['path_history'].append(self.player['room_path'])
        self.player['room_path'] = f"room_{hashlib.md5((self.player['room_path']+door_f).encode()).hexdigest()[:6]}"
        self.player['depth'] += 1; self.generate_room(self.player['room_path'], dt); self.save_player(self.player)
        print(f"Depth {self.player['depth']} reached.")

    def backtrack(self):
        if not self.player['path_history']: return
        p = self.player['path_history'].pop(); self.player['depth'] = max(0, self.player['depth'] - 1)
        self.player['room_path'] = p; self.generate_room(p, is_backtrack=True); self.save_player(self.player)

    def sell_key(self):
        if self.player['keys'] > 0:
            self.player['keys'] -= 1; self.player['xp'] += 50
            print("Key -> 50 XP."); self.save_player(self.player)

    def buy_key(self):
        if self.player['xp'] >= 100:
            self.player['xp'] -= 100; self.player['keys'] += 1
            print("100 XP -> Key."); self.save_player(self.player)
        else: print("Need 100 XP.")

    def terminate(self):
        print("RUN TERMINATED."); self.globals['total_xp'] += self.player['xp']; self.save_global()
        if self.player['depth'] > 0 and os.path.exists(PLAYER_FILE): os.remove(PLAYER_FILE)
        if os.path.exists(COMBAT_FILE): os.remove(COMBAT_FILE)
        sys.exit()

    def upgrade(self, stat):
        cost = 200
        if self.globals['total_xp'] >= cost:
            self.globals['total_xp'] -= cost
            if stat == "hp": self.globals['base_hp'] += 10; print("Base HP Up!")
            elif stat == "atk": self.globals['base_atk'] += 2; print("Base ATK Up!")
            self.save_global()
        else: print("Need 200 Global XP.")

    def show_status(self):
        p = self.player
        print(f"\n{Colors.BOLD}--- RUN DEPTH {p['depth']} --- XP: {Colors.YELLOW}{p['xp']}{Colors.END} | LVL: {Colors.CYAN}{p['lvl']}{Colors.END} | CLASS: {Colors.PURPLE}{p['class']}{Colors.END}")
        
        hp_color = Colors.GREEN if p['hp'] > p['max_hp'] * 0.5 else Colors.RED
        print(f"HP: {hp_color}{p['hp']}/{p['max_hp']}{Colors.END} | ATK: {Colors.YELLOW}{p['atk']}{Colors.END} | DR: {p['dr']} | DODGE: {p['dodge']}% | CRIT: {p['crit']}%")
        
        print(f"MEMORY: {Colors.BOLD}{p['mem_used']}B Used{Colors.END} | {p['fragmentation']}B Holes | {p['mem_capacity']}B Cap")
        print(f"BUFFER: {[i['name'] for i in p['inventory']]}")
        print(f"GLOBAL XP: {Colors.YELLOW}{self.globals['total_xp']}{Colors.END} | BASE: {self.globals['base_hp']}HP/{self.globals['base_atk']}ATK")
        print(f"-------------------\n")

if __name__ == "__main__":
    engine = DelveEngine()
    if len(sys.argv) < 2: engine.show_status(); sys.exit()
    cmd = sys.argv[1]
    if cmd == "--init": engine.reset_run(); engine.generate_room("start"); print("Init.")
    elif cmd == "--enter": engine.enter_room(sys.argv[2])
    elif cmd == "--attack": engine.attack_init(sys.argv[2])
    elif cmd == "--op": engine.combat_turn(sys.argv[2])
    elif cmd == "--loot": engine.loot(sys.argv[2])
    elif cmd == "--use": engine.use_item(sys.argv[2])
    elif cmd == "--defrag": engine.defrag()
    elif cmd == "--skill" and sys.argv[2] == "symlink": engine.symlink()
    elif cmd == "--upgrade": engine.upgrade(sys.argv[2])
    elif cmd == "--status": engine.show_status()
    elif cmd == "--panic":
        if engine.player['xp'] >= 500:
            engine.player['xp'] -= 500; engine.player['room_path'] = "start"; engine.player['depth'] = 0
            engine.player['path_history'] = []; engine.generate_room("start")
            print(">> SYSTEM PANIC: Emergency exit to Start Sector initiated."); engine.save_player(engine.player)
        else: print("Need 500 XP to Panic.")
    elif cmd == "--overclock":
        if os.path.exists(COMBAT_FILE):
            if engine.player['xp'] >= 2000:
                engine.player['xp'] -= 2000
                with open(COMBAT_FILE, "r") as f: c = json.load(f)
                c['lock_turns'] = 10; c['mob_atk'] = 0 # Full stun
                with open(COMBAT_FILE, "w") as f: json.dump(c, f, indent=4)
                print(">> SYSTEM OVERCLOCK: Sacrificing XP to freeze enemy core. (Stunned for 10 turns)"); engine.save_player(engine.player)
            else: print("Need 2000 XP to Overclock.")
        else: print("No combat active.")
    elif cmd == "--purge-cmd":
        if os.path.exists(COMBAT_FILE):
            with open(COMBAT_FILE, "r") as f: c = json.load(f)
            if c['mob_hp'] < (c['mob_max_hp'] * 0.25):
                print(f">> ROOT PURGE: Executing total system wipe on {c['mob_name']}...")
                c['mob_hp'] = 0; engine.player['xp'] = 0
                with open(COMBAT_FILE, "w") as f: json.dump(c, f, indent=4)
                engine.combat_turn("MOV") # Trigger victory logic
            else: print("Enemy HP too high for Purge (Need < 25%).")
        else: print("No combat active.")
    elif cmd == "--sell-key": engine.sell_key()
    elif cmd == "--buy-key": engine.buy_key()
    elif cmd == "--back": engine.backtrack()
