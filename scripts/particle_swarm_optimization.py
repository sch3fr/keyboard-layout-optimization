import json
import random
import copy
import numpy as np
from typing import Dict, List, Tuple

# Importuje kalkulátor
from cost_calculator import (
    QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, 
    calculate_total_cost, ANATOMY_MAP
)

# --- Hyperparametry PSO ---
SWARM_SIZE = 40        # Počet částic v hejnu
ITERATIONS = 100        # Počet generací
C1 = 0.6               # Váha osobní zkušenosti (táhnutí k pBest)
C2 = 0.8               # Váha sociální zkušenosti (táhnutí k gBest)
W = 0.4                # Setrvačnost (kolik náhodných změn si nechá)

# --- Pomocné funkce ---

def get_swap_sequence(current_layout: Dict[str, str], target_layout: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Vypočítá 'vektor rozdílu' mezi dvěma layouty.
    Vrátí seznam dvojic znaků (swapů), které musíme prohodit, 
    abychom dostali z current_layout -> target_layout.
    """
    swaps = []
    # Pracuje s kopií, abychom simulovali kroky
    temp_layout = current_layout.copy()
    
    # Získá inverzní mapování (pozice -> znak) pro rychlé hledání
    pos_to_char = {v: k for k, v in temp_layout.items()}
    
    target_items = list(target_layout.items())
    
    for char, target_pos in target_items:
        if char == ' ': continue # Mezeru neřeší
        
        current_pos = temp_layout[char]
        
        # Pokud je znak jinde, než má být v cíli
        if current_pos != target_pos:
            # Zjistí, kdo teď sedí na cílové pozici
            char_at_target = pos_to_char[target_pos]
            
            # Zaznamená swap (prohodí znak s tím, kdo mu 'zasedl' místo)
            swaps.append((char, char_at_target))
            
            # Provede swap virtuálně v temp_layout
            temp_layout[char] = target_pos
            temp_layout[char_at_target] = current_pos
            
            # Aktualizuje inverzní mapu
            pos_to_char[target_pos] = char
            pos_to_char[current_pos] = char_at_target
            
    return swaps

def apply_swaps_probabilistically(layout: Dict[str, str], swaps: List[Tuple[str, str]], probability: float):
    """
    Aplikuje swapy ze seznamu s určitou pravděpodobností.
    To simuluje 'rychlost' pohybu směrem k cíli.
    """
    new_layout = layout.copy()
    for c1, c2 in swaps:
        if random.random() < probability:
            # Provede swap
            pos1 = new_layout[c1]
            pos2 = new_layout[c2]
            new_layout[c1] = pos2
            new_layout[c2] = pos1
    return new_layout

def quick_local_search(layout: Dict[str, str], chars_to_swap: List[str], max_steps: int = 30):
    """
    Hybridní část: Rychlý Hill Climbing pro dotažení detailů.
    Bez tohoto by PSO jen 'kroužilo' kolem řešení.
    """
    current_layout = layout.copy()
    current_cost = calculate_total_cost(current_layout, UNIGRAM_DATA, TRIGRAM_DATA)
    
    for _ in range(max_steps):
        c1, c2 = random.sample(chars_to_swap, 2)
        
        # Virtuální swap
        test_layout = current_layout.copy()
        test_layout[c1], test_layout[c2] = test_layout[c2], test_layout[c1] # Swap pozic
        
        new_cost = calculate_total_cost(test_layout, UNIGRAM_DATA, TRIGRAM_DATA)
        
        if new_cost < current_cost:
            current_cost = new_cost
            current_layout = test_layout
            
    return current_layout, current_cost

# --- Třída Částice (Particle) ---
class Particle:
    def __init__(self, start_layout, swappable_chars):
        self.layout = start_layout
        self.cost = calculate_total_cost(self.layout, UNIGRAM_DATA, TRIGRAM_DATA)
        
        # Osobní rekord (pBest)
        self.pbest_layout = copy.deepcopy(self.layout)
        self.pbest_cost = self.cost
        
        self.swappable_chars = swappable_chars

    def update(self, gbest_layout):
        """Hlavní logika pohybu částice"""
        
        # 1. Spočítá 'vektory' (seznamy swapů) k cílům
        swaps_to_pbest = get_swap_sequence(self.layout, self.pbest_layout)
        swaps_to_gbest = get_swap_sequence(self.layout, gbest_layout)
        
        # 2. Pohyb (aplikace swapů s pravděpodobností podle C1 a C2)
        # Nejdřív zkusí jít směrem k osobnímu rekordu
        self.layout = apply_swaps_probabilistically(self.layout, swaps_to_pbest, C1)
        # Pak zkusí jít směrem k globálnímu rekordu
        self.layout = apply_swaps_probabilistically(self.layout, swaps_to_gbest, C2)
        
        # 3. Mutace / Setrvačnost (W)
        # S malou pravděpodobností udělá náhodný pohyb v prostoru
        if random.random() < W:
            c1, c2 = random.sample(self.swappable_chars, 2)
            # Prohození pozic
            self.layout[c1], self.layout[c2] = self.layout[c2], self.layout[c1]
            
        # 4. HYBRIDIZACE (Hill Climbing)
        self.layout, self.cost = quick_local_search(self.layout, self.swappable_chars)
        
        # 5. Aktualizace pBest
        if self.cost < self.pbest_cost:
            self.pbest_cost = self.cost
            self.pbest_layout = copy.deepcopy(self.layout)

# --- Hlavní smyčka PSO ---
def pso_optimize():
    # Příprava dat
    swappable_chars = [c for c in QWERTZ_LAYOUT.keys() if c != ' ']
    space_char = ' '
    space_pos = QWERTZ_LAYOUT.get(' ', 'KEY_SPACE') # Zajištění, že víme kde je mezera
    
    # 1. Inicializace hejna
    swarm = []
    print(f"--- Spouštím Hybridní PSO ({SWARM_SIZE} částic) ---")
    
    # Vytvoří náhodné startovní pozice
    for _ in range(SWARM_SIZE):
        # Náhodné rozházení kláves (kromě mezery)
        random_layout = QWERTZ_LAYOUT.copy()
        
        # Získá všechny pozice kromě mezery
        positions = [v for k, v in QWERTZ_LAYOUT.items() if k != ' ']
        random.shuffle(positions)
        
        # Přiřadí
        for i, char in enumerate(swappable_chars):
            random_layout[char] = positions[i]
        
        # Zajistí mezeru
        random_layout[space_char] = space_pos
            
        part = Particle(random_layout, swappable_chars)
        swarm.append(part)

    # Inicializace gBest (Globální rekord)
    gbest_layout = copy.deepcopy(swarm[0].layout)
    gbest_cost = swarm[0].cost
    
    # Najde nejlepší startovní
    for part in swarm:
        if part.cost < gbest_cost:
            gbest_cost = part.cost
            gbest_layout = copy.deepcopy(part.layout)

    print(f"Startovní nejlepší náklad: {gbest_cost:.4f}")

    # 2. Hlavní cyklus
    for i in range(ITERATIONS):
        for part in swarm:
            # Pohni částicí (včetně lokálního hledání)
            part.update(gbest_layout)
            
            # Zkontroluj, jestli nepřekonala globální rekord
            if part.cost < gbest_cost:
                gbest_cost = part.cost
                gbest_layout = copy.deepcopy(part.layout)
                print(f"Gen {i+1:3}: 🚀 Nový gBest náklad: {gbest_cost:.4f}")
        
        # Volitelně: Můžeme měnit parametry v čase (zmenšovat W pro zpřesnění)
        global W
        W = max(0.1, W * 0.98) # Pomalé snižování chaosu

    return gbest_layout, gbest_cost

if __name__ == "__main__":
    try:
        best_layout, best_cost = pso_optimize()
        print(f"\n✅ PSO dokončeno.")
        print(f"🏆 NEJLEPŠÍ NÁKLAD: {best_cost:.4f}")
        
        with open("pso_best_layout.json", "w", encoding="utf-8") as f:
            json.dump(best_layout, f, indent=4, ensure_ascii=False)
            print("Výsledek uložen do 'pso_best_layout.json'.")
            
    except Exception as e:
        print(f"\n❌ Chyba: {e}")