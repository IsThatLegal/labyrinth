import os
import sys
import random
import json
import hashlib
import time
import copy

# Configuration
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_FILE = os.path.join(GAME_DIR, "player_stats.json")
GLOBAL_FILE = os.path.join(GAME_DIR, "global_stats.json")
LOG_FILE = os.path.join(GAME_DIR, "session_log.json")
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
    0x70: {"name": "[BOSS] Race Condition", "hp": 400, "atk": 45, "xp": 1500, "traits": ["multi_strike"]},
    0x80: {"name": "[BOSS] Null Pointer Overlord", "hp": 500, "atk": 40, "xp": 2000, "traits": ["true_dmg"]},
    0x90: {"name": "[BOSS] Kernel Panic Archon", "hp": 600, "atk": 50, "xp": 3000, "traits": ["crit", "true_dmg"]},
}
ITEMS = {
    0x20: {"name": "Cache_Patch", "type": "heal", "value": 15, "desc": "Restores 15 HP"},
    0x23: {"name": "Sector_Key", "type": "key", "desc": "Unlocks encrypted doors."},
    0x30: {"name": "Logic_Blade", "type": "buff", "stat": "atk", "value": 3, "desc": "+3 ATK (Root)"},
    0x31: {"name": "Compiler_Loop", "type": "buff", "stat": "xp", "value": 50, "desc": "+50 Instant XP (Root)"},
    0x32: {"name": "Syntax_Lens", "type": "buff", "stat": "crit", "value": 2, "desc": "+2% Crit (Root)"},
    0x40: {"name": "Protocol_Shield", "type": "buff", "stat": "max_hp", "value": 15, "dr": 1, "desc": "+15 Max HP & 1 DR (Firewall)"},
    0x41: {"name": "Heavy_Kernel", "type": "buff", "stat": "max_hp", "value": 30, "desc": "+30 Max HP (Firewall)"},
    0x42: {"name": "Iron_Clad_Mesh", "type": "buff", "stat": "dr", "value": 2, "desc": "+2 Damage Reduction (Firewall)"},
    0x50: {"name": "Reflex_Buffer", "type": "buff", "stat": "dodge", "value": 5, "desc": "+5% Dodge (Exploit)"},
    0x51: {"name": "Zero_Day_Shiv", "type": "buff", "stat": "crit", "value": 5, "desc": "+5% Crit (Exploit)"},
    0x52: {"name": "Ghost_Protocol", "type": "buff", "stat": "dodge", "value": 3, "atk": 1, "desc": "+3% Dodge & +1 ATK (Exploit)"},
}
COMPILED_ITEMS = {
    "Nano_Regen": {"type": "heal", "value": 100, "shield": 2, "desc": "Full Heal + 2-turn Invulnerability"},
    "Void_Edge": {"type": "buff", "stat": "atk", "value": 10, "percent_dmg": 0.05, "desc": "+10 ATK & 5% Max HP True Damage"},
    "Aegis_Firewall": {"type": "buff", "stat": "max_hp", "value": 50, "dr": 20, "desc": "+50 Max HP & 20 Damage Reduction"},
}
DOOR_TYPES = {
    "ROOT": {"desc": "A pulsing data stream promising POWER.", "loot_table": [0x30, 0x31, 0x32]},
    "FIREWALL": {"desc": "A heavily reinforced blast door promising DEFENSE.", "loot_table": [0x40, 0x41, 0x42]},
    "EXPLOIT": {"desc": "A glitching, unstable rift promising AGILITY.", "loot_table": [0x50, 0x51, 0x52]},
}
RARITIES = {
    "COMMON": {"chance": 0.70, "stat_mult": 1.0, "xp_mult": 1, "color": ""},
    "RARE": {"chance": 0.20, "stat_mult": 1.5, "xp_mult": 2, "color": "[RARE] "},
    "ELITE": {"chance": 0.08, "stat_mult": 2.5, "xp_mult": 5, "color": "[ELITE] "},
    "LEGENDARY": {"chance": 0.02, "stat_mult": 5.0, "xp_mult": 20, "color": "[LEGENDARY] "},
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
                p.setdefault("class", "Novice")
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
            "class": "Novice"
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

    def compile_item(self, item_name):
        recipe_map = {"Cache_Patch": "Nano_Regen", "Logic_Blade": "Void_Edge", "Protocol_Shield": "Aegis_Firewall"}
        if item_name not in recipe_map: print("Invalid recipe."); return
        if self.player['xp'] < 150: print("Need 150 XP."); return
        for i, it in enumerate(self.player['inventory']):
            if it['name'] == item_name:
                self.player['inventory'].pop(i); self.player['xp'] -= 150
                new_item = copy.deepcopy(COMPILED_ITEMS[recipe_map[item_name]])
                new_item['name'] = recipe_map[item_name]
                self.player['inventory'].append(new_item)
                print(f"Compiled {item_name} into {new_item['name']}!"); self.save_player(self.player); return
        print("Item not found in buffer.")

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

    def attack(self, mob_filename):
        mob_path = os.path.join(GAME_DIR, self.player['room_path'], "mobs", mob_filename)
        if not os.path.exists(mob_path): return
        with open(mob_path, "r") as f: mob = json.load(f)
        print(f"--- COMBAT: {mob['name']} ---")
        traits = mob.get('traits', [])
        while mob['hp'] > 0 and self.player['hp'] > 0:
            dmg = self.player['atk'] * (2 if self.player['overclocked'] else 1)
            dmg += int(mob['hp'] * self.player['percent_dmg'])
            if random.random() < (self.player['crit'] / 100.0): dmg *= 2; print("CRITICAL!")
            self.player['overclocked'] = False; mob['hp'] -= dmg
            print(f"You strike for {dmg}! ({max(0, mob['hp'])} HP left)")
            if mob['hp'] <= 0:
                print(f"Purged! +{mob['xp']} XP"); self.player['xp'] += mob['xp']
                self.player['battles_won'] += 1; self.check_level_up()
                if self.player['depth'] >= 20: self.player['corruption'] = max(0, self.player['corruption'] - 10)
                if random.random() < 0.25: self.player['keys'] += 1
                os.remove(mob_path); break
            if self.player['shield_turns'] > 0:
                self.player['shield_turns'] -= 1; print("SHIELD ABSORBED!")
            else:
                hit = True
                if "true_dmg" not in traits:
                    if random.random() < (self.player['dodge'] / 100.0): print("EVADED!"); hit = False
                else: print("UNAVOIDABLE!")
                if hit:
                    mob_atk = mob['atk']
                    if "crit" in traits and random.random() < 0.25: mob_atk *= 2; print("ENEMY CRIT!")
                    final_dmg = max(1, mob_atk - self.player['dr'])
                    self.player['hp'] -= final_dmg; print(f"Took {final_dmg} DMG ({self.player['hp']}/{self.player['max_hp']} HP)")
                    if "drain" in traits:
                        lost = 20; self.player['xp'] = max(0, self.player['xp'] - lost); print(f"DRAINED: Lost {lost} XP.")
                    if "lifesteal" in traits:
                        heal = final_dmg; mob['hp'] += heal; print(f"LIFESTEAL: Boss repaired {heal} integrity.")
                    if "multi_strike" in traits and random.random() < 0.3:
                        self.player['hp'] -= final_dmg; print(f"RACE CONDITION: Double strike! Took another {final_dmg} DMG.")
        if self.player['hp'] <= 0: self.terminate()
        self.save_player(self.player)

    def use_item(self, item_name):
        for i, it in enumerate(self.player['inventory']):
            if it['name'] == item_name:
                item = self.player['inventory'].pop(i)
                if item['type'] == "heal":
                    v = item['value']; self.player['hp'] = min(self.player['max_hp'], self.player['hp'] + v)
                    if 'shield' in item: self.player['shield_turns'] += item['shield']
                    print(f"HP Restored. Shield: {self.player['shield_turns']}")
                elif item['type'] == "buff":
                    self.player[item['stat']] += item['value']
                    if 'percent_dmg' in item: self.player['percent_dmg'] += item['percent_dmg']
                    if 'dr' in item: self.player['dr'] += item['dr']
                    if item['stat'] == "max_hp": self.player['hp'] += item['value']
                    if item['stat'] == "xp": self.player['xp'] += item['value']
                    if 'atk' in item and item['stat'] != 'atk': self.player['atk'] += item['atk']
                    print(f"Applied {item['name']}.")
                elif item['type'] == "key": self.player['keys'] += 1
                self.save_player(self.player); return
        print("Item not found.")

    def skill(self, skill_name):
        costs = {"stealth": 50, "overclock": 75, "purge": 100}
        if self.player['xp'] < costs.get(skill_name, 999): print("Low XP."); return
        self.player['xp'] -= costs[skill_name]
        if skill_name == "stealth": self.player['skills'] = {"stealth": 1}
        elif skill_name == "overclock": self.player['overclocked'] = True
        elif skill_name == "purge": self.player['corruption'] = max(0, self.player['corruption'] - 30)
        self.save_player(self.player); print(f"Activated {skill_name}.")

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
        if depth > 0 and depth < 100 and depth % 10 == 0:
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
            it = ITEMS[0x40] # Protocol Shield guarantee
            with open(os.path.join(items_dir, f"{it['name']}.json"), "w") as f: json.dump(it, f, indent=4)
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
        mobs_dir = os.path.join(GAME_DIR, self.player['room_path'], "mobs")
        active = os.listdir(mobs_dir) if os.path.exists(mobs_dir) else []
        door_path = os.path.join(GAME_DIR, self.player['room_path'], "doors", door_f)
        if os.path.exists(door_path):
            with open(door_path, "r") as f: d_data = f.read()
            if "LOCKED: True" in d_data:
                if self.player['keys'] > 0: self.player['keys'] -= 1; print("Unlocked.")
                else: print("LOCKED."); return
        if active:
            if self.player.get('skills', {}).get('stealth', 0) > 0: self.player['skills']['stealth'] = 0; print("Stealth used.")
            else:
                if random.random() < 0.6:
                    with open(os.path.join(mobs_dir, active[0]), "r") as f: mob = json.load(f)
                    if self.player['shield_turns'] > 0: self.player['shield_turns'] -= 1; print("Shield absorbed!")
                    elif random.random() < (self.player['dodge'] / 100.0): print("EVADED!")
                    else:
                        self.player['hp'] -= mob['atk']; print(f"Intercepted by {mob['name']}! Took {mob['atk']} DMG.")
                        if self.player['hp'] <= 0: self.terminate()
        if not os.path.exists(door_path): return
        with open(door_path, "r") as f: dt = f.readlines()[0].split(": ")[1].strip()
        self.player['path_history'].append(self.player['room_path'])
        self.player['room_path'] = f"room_{hashlib.md5((self.player['room_path']+door_f).encode()).hexdigest()[:6]}"
        self.player['depth'] += 1; self.generate_room(self.player['room_path'], dt); self.save_player(self.player)
        print(f"Depth {self.player['depth']} reached.")

    def loot(self, item_filename):
        item_path = os.path.join(GAME_DIR, self.player['room_path'], "items", item_filename)
        if not os.path.exists(item_path): return
        with open(item_path, "r") as f: item = json.load(f)
        print(f"Buffer + {item['name']}"); self.player['inventory'].append(item)
        os.remove(item_path); self.save_player(self.player)

    def backtrack(self):
        if not self.player['path_history']: return
        p = self.player['path_history'].pop(); self.player['depth'] = max(0, self.player['depth'] - 1)
        self.player['room_path'] = p; self.generate_room(p, is_backtrack=True); self.save_player(self.player)

    def sell_key(self):
        if self.player['keys'] > 0: self.player['keys'] -= 1; self.player['xp'] += 50; print("Key -> 50 XP."); self.save_player(self.player)

    def buy_key(self):
        if self.player['xp'] >= 100: self.player['xp'] -= 100; self.player['keys'] += 1; print("100 XP -> Key."); self.save_player(self.player)
        else: print("Need 100 XP.")

    def terminate(self):
        print("RUN TERMINATED."); self.globals['total_xp'] += self.player['xp']; self.save_global()
        if self.player['depth'] > 0 and os.path.exists(PLAYER_FILE): os.remove(PLAYER_FILE)
        sys.exit()

    def upgrade(self, stat):
        cost = 200
        if self.globals['total_xp'] >= cost:
            self.globals['total_xp'] -= cost
            if stat == "hp": self.globals['base_hp'] += 10; print("Base HP Up!")
            elif stat == "atk": self.globals['base_atk'] += 2; print("Base ATK Up!")
            self.save_global()
        else: print("Need 200 Global XP.")

    def boss_init(self):
        boss_hp = 500 + (self.player['keys'] * 50) + (self.player['xp'] // 2)
        state = {"name": "THE KEY DEVOURER", "hp": boss_hp, "max_hp": boss_hp, "atk": 25, "phase": 1, "grasp_active": False, "active": True}
        with open(os.path.join(GAME_DIR, "boss_state.json"), "w") as f: json.dump(state, f, indent=4)
        print(f"!!! THE CORE TREMBLES !!!\nTHE KEY DEVOURER MANIFESTS. HP: {boss_hp}\nUse --boss-action <1:Strike, 2:Mitigate, 3:Empower, 4:Reconstruct>")

    def boss_turn(self, action):
        state_path = os.path.join(GAME_DIR, "boss_state.json")
        if not os.path.exists(state_path): print("No boss active. Use --boss-start"); return
        with open(state_path, "r") as f: boss = json.load(f)
        if self.player['hp'] <= 0 or not boss['active']: print("The battle is over."); return
        p, mitigating, p_dmg = self.player, False, self.player['atk']
        if action == "2":
            if boss['grasp_active']: print(">> GRASPED! You cannot mitigate damage right now!")
            elif p['keys'] > 0: p['keys'] -= 1; mitigating = True; print(f">> MITIGATE: Used 1 Key. Damage will be halved.")
            else: print(">> NO KEYS left to mitigate with!")
        elif action == "3":
            if boss['grasp_active']: print(">> GRASPED! You cannot empower your strikes right now!")
            elif p['keys'] > 0: p['keys'] -= 1; p_dmg *= 2; print(f">> EMPOWER: Used 1 Key. Strike power doubled!")
            else: print(">> NO KEYS left to empower with!")
        elif action == "4":
            if p['xp'] >= 100: p['xp'] -= 100; p['hp'] = min(p['max_hp'], p['hp'] + 50); print(f">> RECONSTRUCT: Data segments repaired. +50 HP ({p['hp']}/{p['max_hp']})")
            else: print(">> NO XP left to reconstruct with!")
        elif action != "1": print("Invalid action. Strike [1], Mitigate [2], Empower [3], Reconstruct [4]"); return
        boss['grasp_active'] = False
        if p['overclocked']: p_dmg *= 2; p['overclocked'] = False
        if random.random() < (p['crit'] / 100.0): p_dmg *= 2; print("CRITICAL!")
        boss['hp'] -= p_dmg; print(f"You strike the Devourer for {p_dmg} DMG! ({max(0, boss['hp'])} HP left)")
        if boss['hp'] <= 0:
            print("\n*** THE KEY DEVOURER DISSIPATES INTO PURE DATA ***\nLabyrinth Cleared. You have mastered the Core."); self.globals['total_xp'] += 2000; self.save_global(); boss['active'] = False; os.remove(state_path); self.save_player(p); return
        new_phase = 1
        if boss['hp'] < boss['max_hp'] * 0.33: new_phase = 3
        elif boss['hp'] < boss['max_hp'] * 0.66: new_phase = 2
        if new_phase > boss['phase']: boss['phase'] = new_phase; print(f"!!! BOSS EVOLVING: PHASE {boss['phase']} !!!"); boss['atk'] += 10
        if boss['phase'] >= 2 and random.random() < 0.4:
            if p['keys'] > 0: p['keys'] -= 1; boss['hp'] = min(boss['max_hp'], boss['hp'] + 40); boss['atk'] += 2; print(">> CONSUME KEY: The boss ate one of your keys and repaired itself!")
            else: print(">> CONSUME KEY: You have no keys! The Devourer screams in frustration (+5 ATK)."); boss['atk'] += 5
        if (boss['phase'] == 1 or boss['phase'] == 3) and random.random() < 0.3: drain = 30; p['xp'] = max(0, p['xp'] - drain); print(f">> RESOURCE DRAIN: Your buffer leaked {drain} XP into the void.")
        if boss['phase'] == 3 and random.random() < 0.3: boss['grasp_active'] = True; print(">> DEVOURER'S GRASP: Dark code binds your resources! (Choices disabled next turn)")
        boss_atk = boss['atk'] // 2 if mitigating else boss['atk']
        p['hp'] -= boss_atk; print(f"THE DEVOURER STRIKES: Took {boss_atk} DMG ({p['hp']}/{p['max_hp']} HP)")
        if p['hp'] <= 0: print("\n[!] FATAL ERROR: YOU HAVE BEEN DEVOURED."); self.terminate()
        with open(state_path, "w") as f: json.dump(boss, f, indent=4)
        self.save_player(p)

    def show_status(self):
        p = self.player
        print(f"\n--- RUN DEPTH {p['depth']} --- XP: {p['xp']} | LVL: {p['lvl']} | CLASS: {p['class']}")
        print(f"HP: {p['hp']}/{p['max_hp']} | ATK: {p['atk']} | DR: {p['dr']} | DODGE: {p['dodge']}% | CRIT: {p['crit']}%")
        print(f"BUFFER: {[i['name'] for i in p['inventory']]}")
        print(f"GLOBAL XP: {self.globals['total_xp']} | BASE: {self.globals['base_hp']}HP/{self.globals['base_atk']}ATK")
        print(f"-------------------\n")

if __name__ == "__main__":
    engine = DelveEngine()
    if len(sys.argv) < 2: engine.show_status(); sys.exit()
    cmd = sys.argv[1]
    if cmd == "--init": engine.reset_run(); engine.generate_room("start"); print("Init.")
    elif cmd == "--enter": engine.enter_room(sys.argv[2])
    elif cmd == "--attack": engine.attack(sys.argv[2])
    elif cmd == "--loot": engine.loot(sys.argv[2])
    elif cmd == "--use": engine.use_item(sys.argv[2])
    elif cmd == "--compile": engine.compile_item(sys.argv[2])
    elif cmd == "--skill": engine.skill(sys.argv[2])
    elif cmd == "--upgrade": engine.upgrade(sys.argv[2])
    elif cmd == "--status": engine.show_status()
    elif cmd == "--sell-key": engine.sell_key()
    elif cmd == "--buy-key": engine.buy_key()
    elif cmd == "--back": engine.backtrack()
    elif cmd == "--boss-start": engine.boss_init()
    elif cmd == "--boss-action": engine.boss_turn(sys.argv[2])
