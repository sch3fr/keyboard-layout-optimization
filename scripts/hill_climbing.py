# optimalizační skript metodou Hill climbing

import json
import random
from typing import Dict, List, Tuple

# předpokládá, že soubor cost_calculator.py je ve stejné složce
from cost_calculator import QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, calculate_total_cost 

# nastavení omezení pro hill climbing
MAX_ITERATIONS = 200 

# generování sousedů

def get_all_neighbors(current_layout: Dict[str, str], swappable_chars: List[str]) -> List[Dict[str, str]]:
    """
    Generuje všechna sousední rozložení (swapy) POUZE mezi znaky uvedenými ve swappable_chars.
    """
    # swappable_chars existuje proto, aby optimalizace neměnila pozici mezerníku

    neighbors = []
    n = len(swappable_chars)
    
    # generování všech možných dvojic znaků pro záměnu
    for i in range(n):
        for j in range(i + 1, n):
            char1 = swappable_chars[i]
            char2 = swappable_chars[j]

            new_layout = current_layout.copy()
            
            # hledá pozice pro provedení SWAPU
            pos1 = current_layout[char1]
            pos2 = current_layout[char2]

            # provádí SWAP (výměnu pozic)
            new_layout[char1] = pos2
            new_layout[char2] = pos1
            
            neighbors.append(new_layout)
            
    return neighbors

# hlavní algoritmus Hill Climbing 

def hill_climbing_optimize(start_layout: Dict[str, str], unigram_data: Dict[str, float], trigram_data: Dict[str, float], swappable_chars: List[str]) -> Tuple[Dict[str, str], float, int]:
    """
    Spustí algoritmus Hill Climbing (Best-Choice) s definovanými znaky pro optimalizaci.
    """
    current_layout = start_layout.copy()
    current_cost = calculate_total_cost(current_layout, unigram_data, trigram_data)
    print(f"Startovní náklad (QWERTZ): {current_cost:.4f}")

    iterations = 0
    
    while iterations < MAX_ITERATIONS:
        iterations += 1
        
        # generuje všechny sousedy POUZE ze swappable_chars
        neighbors = get_all_neighbors(current_layout, swappable_chars)
        
        best_neighbor = None
        best_neighbor_cost = current_cost
        
        # hledá nejlepšího souseda (Best-Choice)
        for neighbor_layout in neighbors:
            neighbor_cost = calculate_total_cost(neighbor_layout, unigram_data, trigram_data)
            
            if neighbor_cost < best_neighbor_cost:
                best_neighbor_cost = neighbor_cost
                best_neighbor = neighbor_layout
        
        # posun pokud našel lepší řešení
        if best_neighbor_cost < current_cost:
            current_layout = best_neighbor
            current_cost = best_neighbor_cost
            print(f"Iterace {iterations:2}: Nový náklad = {current_cost:.4f}")
        else:
            # Lokální optimum nalezeno
            break
            
    print(f"\n--- Hill Climbing Hotovo ---")
    print(f"Zastaveno v iteraci {iterations} (nalezeno lokální optimum).")
    
    return current_layout, current_cost, iterations

# spuštění skriptu

if __name__ == "__main__":
    
    print("--- Spouštím Optimalizaci Klávesnice (Hill Climbing) ---")
    
    SWAPPABLE_CHARS = list(QWERTZ_LAYOUT.keys())
    
    # maže mezeru ze seznamu kláves dostupných ke změně pozice
    if ' ' in SWAPPABLE_CHARS:
        SWAPPABLE_CHARS.remove(' ')
        print("POZOR: Znak mezery (' ') byl z optimalizace vyloučen (fixní pozice).")
    
    final_layout, final_cost, total_iter = hill_climbing_optimize(
        start_layout=QWERTZ_LAYOUT, 
        unigram_data=UNIGRAM_DATA,
        trigram_data=TRIGRAM_DATA,
        swappable_chars=SWAPPABLE_CHARS # předává seznam povolených znaků!
    )
    
    print("\n-----------------------------------------------------")
    # ... (tisk výsledků) ...
    print("-----------------------------------------------------")
    
    # Ukládání výsledku (aby byl dostupný)
    with open("hill_climbing_result_layout_fixed.json", "w", encoding="utf-8") as f:
        json.dump(final_layout, f, indent=4, ensure_ascii=False)
        
    print(f"\n✅ Finální rozložení uloženo do: hill_climbing_result_layout_fixed.json")