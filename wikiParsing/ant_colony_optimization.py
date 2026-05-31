import json
import random
import numpy as np
from typing import Dict, List, Tuple


# Importuje závislosti z cost_calculator.py
from cost_calculator import (
    QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, 
    calculate_total_cost, ANATOMY_MAP, POSITIONAL_COSTS
)

# --- Hyperparametry ACO ---
NUM_ANTS = 20          
NUM_ITERATIONS = 100   
EVAPORATION_RATE = 0.4 
ALPHA = 1.0            # Váha feromonu
BETA = 1.5             # Sníženo, aby heuristika "nepřebila" pravděpodobnost do nuly
Q = 10.0               

def get_heuristic_matrix(chars: List[str], positions: List[str]) -> np.ndarray:
    """Vytvoří matici heuristiky (eta). Čím vyšší, tím lepší pozice pro znak."""
    matrix = np.zeros((len(chars), len(positions)))
    max_freq = max(UNIGRAM_DATA.values()) if UNIGRAM_DATA else 1
    
    for i, char in enumerate(chars):
        # Přidává malou konstantu (epsilon), aby frekvence nebyla nikdy čistá nula
        freq = (UNIGRAM_DATA.get(char, 0) / max_freq) + 0.0001
        for j, pos in enumerate(positions):
            if pos in ANATOMY_MAP:
                _, prst, rada = ANATOMY_MAP[pos]
                pos_cost = POSITIONAL_COSTS[rada][prst]
            else:
                pos_cost = 10.0  # Penalizace pro klávesy mimo mapu
            
            # Heuristika: poměr frekvence a ceny pozice
            matrix[i][j] = freq / pos_cost
            
    return matrix

def aco_optimize():
    # 1. Filtrace dat - pracuje jen s tím, co je zadáno v anatomii a layoutu
    all_available_positions = set(ANATOMY_MAP.keys())
    
    # Najde znaky, kterými může hýbat (vše kromě mezery)
    swappable_chars = [c for c in QWERTZ_LAYOUT.keys() if c != ' ']
    
    # Pozice, které jsou volné (vše kromě té, kde je mezera)
    space_pos = QWERTZ_LAYOUT.get(' ', 'KEY_SPACE')
    swappable_positions = [p for p in all_available_positions if p != space_pos]

    # kontrola zda je dostatek pozic pro všechny znaky
    if len(swappable_positions) < len(swappable_chars):
        # Pokud chybí v ANATOMY_MAP klávesy, přidá ty z QWERTZ_LAYOUT
        for char, pos in QWERTZ_LAYOUT.items():
            if pos not in swappable_positions and pos != space_pos:
                swappable_positions.append(pos)

    num_chars = len(swappable_chars)
    num_pos = len(swappable_positions)
    
    # Inicializace
    pheromones = np.ones((num_chars, num_pos))
    heuristics = get_heuristic_matrix(swappable_chars, swappable_positions)
    
    best_overall_layout = None
    best_overall_cost = float('inf')
    
    print(f"--- Start ACO ---")
    print(f"Optimalizuji {num_chars} znaků na {num_pos} pozicích.")

    for gen in range(NUM_ITERATIONS):
        gen_layouts = []
        gen_costs = []
        
        for ant in range(NUM_ANTS):
            ant_layout = {' ': space_pos}
            available_p_indices = list(range(num_pos))
            char_indices = list(range(num_chars))
            random.shuffle(char_indices) # Mravenec bere znaky v náhodném pořadí
            
            mapping = []
            
            for c_idx in char_indices:
                # tau^alpha * eta^beta
                tau = pheromones[c_idx][available_p_indices] ** ALPHA
                eta = heuristics[c_idx][available_p_indices] ** BETA
                probs = tau * eta
                
                # Ošetření NaN/Zero: Pokud je součet 0, nastaví rovnoměrnou pravděpodobnost
                s = probs.sum()
                if s == 0 or np.isnan(s):
                    probs = np.ones(len(available_p_indices)) / len(available_p_indices)
                else:
                    probs /= s
                
                # Výběr pozice
                choice_idx = np.random.choice(len(available_p_indices), p=probs)
                p_idx = available_p_indices.pop(choice_idx)
                
                ant_layout[swappable_chars[c_idx]] = swappable_positions[p_idx]
                mapping.append((c_idx, p_idx))
            
            # Výpočet nákladu
            cost = calculate_total_cost(ant_layout, UNIGRAM_DATA, TRIGRAM_DATA)
            gen_layouts.append((ant_layout, mapping))
            gen_costs.append(cost)
            
            if cost < best_overall_cost:
                best_overall_cost = cost
                best_overall_layout = ant_layout.copy()
                print(f"Gen {gen+1:3}: Nový rekord: {best_overall_cost:.4f}")

        # Odpařování a aktualizace feromonů
        pheromones *= (1 - EVAPORATION_RATE)
        for i, (layout, mapping) in enumerate(gen_layouts):
            # Mravenci s nižším nákladem zanechají více feromonů
            deposit = Q / gen_costs[i]
            for c_idx, p_idx in mapping:
                pheromones[c_idx][p_idx] += deposit

    return best_overall_layout, best_overall_cost

if __name__ == "__main__":
    best_layout, best_cost = aco_optimize()
    print(f"\n✅ Hotovo! Nejlepší náklad: {best_cost:.4f}")
    
    with open("aco_best_layout.json", "w", encoding="utf-8") as f:
        json.dump(best_layout, f, indent=4, ensure_ascii=False)