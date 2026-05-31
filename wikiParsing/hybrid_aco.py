import json
import random
import numpy as np
from typing import Dict, List, Tuple
import hill_climbing_fixed

# Importuje počítadlo nákladu

from cost_calculator import (
    QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, 
    calculate_total_cost, ANATOMY_MAP, POSITIONAL_COSTS
)

# --- Hyperparametry ACO ---
NUM_ANTS = 15          # Počet mravenců
NUM_ITERATIONS = 50    # Počet generací
EVAPORATION_RATE = 0.4 # Odpařování feromonů
ALPHA = 1.0            # Váha feromonu (zkušenost kolonie)
BETA = 1.5             # Váha heuristiky (chamtivost po unigramech)
Q = 10.0               # Množství feromonu k rozstřiku

# --- 1. Pomocná funkce: Heuristická Matice ---
def get_heuristic_matrix(chars: List[str], positions: List[str]) -> np.ndarray:
    """
    Vytvoří matici 'lákavosti' pozic.
    Kombinuje frekvenci znaku a ergonomickou cenu pozice.
    """
    matrix = np.zeros((len(chars), len(positions)))
    max_freq = max(UNIGRAM_DATA.values()) if UNIGRAM_DATA else 1
    
    for i, char in enumerate(chars):
        # Epsilon +0.0001 zajistí, že se nikdy nedělí nulou nebo není nulová šance
        freq = (UNIGRAM_DATA.get(char, 0) / max_freq) + 0.0001
        for j, pos in enumerate(positions):
            if pos in ANATOMY_MAP:
                _, prst, rada = ANATOMY_MAP[pos]
                pos_cost = POSITIONAL_COSTS[rada][prst]
            else:
                pos_cost = 10.0 # Penalizace pro neznámé klávesy
            
            # Heuristika = Frekvence / Cena pozice
            matrix[i][j] = freq / pos_cost
            
    return matrix

# --- 2. Pomocná funkce: Rychlé Lokální Hledání (Hybridizace) ---
def quick_local_search(layout: Dict[str, str], chars_to_swap: List[str], max_steps: int = 40):
    """
    Rychlý Hill Climbing, který 'učeše' hrubý návrh mravence.
    Tohle je ten klíč, který dostane náklad pod 3.65!
    """
    current_layout = layout.copy()
    current_cost = calculate_total_cost(current_layout, UNIGRAM_DATA, TRIGRAM_DATA)
    
    for _ in range(max_steps):
        # Vybírá náhodně dva znaky a zkusí je prohodit
        c1, c2 = random.sample(chars_to_swap, 2)
        
        # Provedeme swap jen virtuálně
        pos1 = current_layout[c1]
        pos2 = current_layout[c2]
        
        # Dočasný layout pro výpočet
        # (Optimalizace: nekopíruje celý dict, jen prohodí a vrátí zpět pokud to není lepší)
        # Ale pro jednoduchost a bezpečnost zde použijeme kopii:
        test_layout = current_layout.copy()
        test_layout[c1] = pos2
        test_layout[c2] = pos1
        
        new_cost = calculate_total_cost(test_layout, UNIGRAM_DATA, TRIGRAM_DATA)
        
        if new_cost < current_cost:
            current_cost = new_cost
            current_layout = test_layout
            
    return current_layout, current_cost

# --- 3. Hlavní funkce: ACO Optimalizace ---
def aco_optimize():
    # A. Příprava dat - Sjednocení znaků a pozic
    all_available_positions = set(ANATOMY_MAP.keys())
    
    # Znaky k optimalizaci (vše kromě mezery)
    swappable_chars = [c for c in QWERTZ_LAYOUT.keys() if c != ' ']
    
    # Fixní pozice mezery
    space_char = ' '
    space_pos = QWERTZ_LAYOUT.get(space_char, 'KEY_SPACE')
    
    # Pozice k dispozici (vše kromě pozice mezery)
    swappable_positions = [p for p in all_available_positions if p != space_pos]
    
    # Pokud je více pozic v layoutu než v anatomii, nebo naopak
    # zajistí, že existuje dostatek pozic pro všechny znaky
    if len(swappable_positions) < len(swappable_chars):
        print(f"Varování: Málo anatomických pozic ({len(swappable_positions)}) pro znaky ({len(swappable_chars)}).")
        # Přidá 'fiktivní' pozice z layoutu, aby to nespadlo (i když budou mít vysokou cenu)
        for val in QWERTZ_LAYOUT.values():
            if val not in swappable_positions and val != space_pos:
                swappable_positions.append(val)
    
    # Ořízne počet pozic přesně na počet znaků (pro čtvercovou matici výběru)
    # To zjednodušuje mravencům rozhodování 1:1
    if len(swappable_positions) > len(swappable_chars):
        swappable_positions = swappable_positions[:len(swappable_chars)]

    num_chars = len(swappable_chars)
    num_pos = len(swappable_positions)
    
    # B. Inicializace feromonů a heuristiky
    pheromones = np.ones((num_chars, num_pos))
    heuristics = get_heuristic_matrix(swappable_chars, swappable_positions)
    
    best_overall_layout = None
    best_overall_cost = float('inf')
    
    print(f"--- Spouštím Hybridní ACO ---")
    print(f"Optimalizuji {num_chars} znaků.")

    # C. Hlavní smyčka generací
    for gen in range(NUM_ITERATIONS):
        gen_layouts = []
        gen_costs = []
        
        for ant in range(NUM_ANTS):
            # 1. Mravenec staví řešení
            ant_layout = {space_char: space_pos} # Začátek s fixní mezerou
            
            available_p_indices = list(range(num_pos))
            char_indices = list(range(num_chars))
            random.shuffle(char_indices) # Náhodné pořadí braní znaků
            
            mapping = [] # Ukládá, co mravenec vybral, pro feromony
            
            for c_idx in char_indices:
                # Výpočet pravděpodobnosti: P = (Feromon^Alpha) * (Heuristika^Beta)
                tau = pheromones[c_idx][available_p_indices] ** ALPHA
                eta = heuristics[c_idx][available_p_indices] ** BETA
                probs = tau * eta
                
                # Ošetření nulového součtu (prevence NaN erroru)
                s = probs.sum()
                if s == 0 or np.isnan(s):
                    probs = np.ones(len(available_p_indices)) / len(available_p_indices)
                else:
                    probs /= s
                
                # Ruletový výběr pozice
                choice_idx = np.random.choice(len(available_p_indices), p=probs)
                p_idx = available_p_indices.pop(choice_idx)
                
                # Zápis do layoutu
                char_name = swappable_chars[c_idx]
                pos_name = swappable_positions[p_idx]
                ant_layout[char_name] = pos_name
                mapping.append((c_idx, p_idx))
            
            # 2. HYBRIDIZACE: Rychlé lokální hledání (Hill Climbing)
            # Tímto krokem opraví špatné trigramy, které mravenec 'neviděl'
            improved_layout, final_cost = quick_local_search(ant_layout, swappable_chars)
            
            # Uloží výsledek
            gen_layouts.append((improved_layout, mapping)) # Mapping nechá původní (pro feromony)
            gen_costs.append(final_cost)
            
            # Kontrola rekordu
            if final_cost < best_overall_cost:
                best_overall_cost = final_cost
                best_overall_layout = improved_layout.copy()
                print(f"Gen {gen+1:3}: Nový rekord: {best_overall_cost:.4f}")

        # 3. Aktualizace feromonů
        pheromones *= (1 - EVAPORATION_RATE) # Odpařování
        
        for i, (layout, mapping) in enumerate(gen_layouts):
            # Mravenci s nižším nákladem přidají více feromonu
            deposit = Q / gen_costs[i]
            
            # Feromon dává na cesty, které mravenec původně vybral
            
            for c_idx, p_idx in mapping:
                pheromones[c_idx][p_idx] += deposit

    return best_overall_layout, best_overall_cost

# --- Spuštění ---
if __name__ == "__main__":
    try:
        best_layout, best_cost = aco_optimize()
        print(f"\n✅ Hybridní ACO dokončeno.")
        print(f"🏆 NEJLEPŠÍ NÁKLAD: {best_cost:.4f}")
        
        with open("haco_best_layout.json", "w", encoding="utf-8") as f:
            json.dump(best_layout, f, indent=4, ensure_ascii=False)
            print("Výsledek uložen do 'haco_best_layout.json'.")
            
    except Exception as e:
        print(f"\n❌ Chyba při běhu: {e}")
        print("Zkontroluj, zda máš 'cost_calculator.py' ve stejné složce a zda jsou v něm správně definovaná data.")