# Optimalizační skript simulovaného žíhání

import json
import random
import math
from typing import Dict, List, Tuple

# předpokládá, že soubor cost_calculator.py je ve stejné složce
from cost_calculator import QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, calculate_total_cost 

# Nastavení Hyperparametrů Simulated Annealing
# tyto parametry definují délku a kvalitu prohledávání.
# vyšší T_start, nižší T_end a ALPHA blížící se 1.0 = delší, ale kvalitnější prohledávání.
T_START = 1.0    # počáteční teplota
T_END = 0.00001  # konečná teplota (dostatečně nízká pro konvergenci)
ALPHA = 0.9999   # koeficient chlazení (exponentní schéma)

# pro SA je potřeba generovat jen JEDNOHO náhodného souseda
def generate_random_neighbor(current_layout: Dict[str, str], swappable_chars: List[str]) -> Dict[str, str]:
    """Vybere 2 náhodné znaky a provede jejich záměnu."""
    
    # zvolí náhodně 2 znaky pro swap (pouze z povoleného seznamu)
    char1, char2 = random.sample(swappable_chars, 2)
    
    # vytváří nové rozložení provedením swapu
    new_layout = current_layout.copy()
    pos1 = current_layout[char1]
    pos2 = current_layout[char2]
    new_layout[char1] = pos2
    new_layout[char2] = pos1
    
    return new_layout

def simulated_annealing_optimize(
    start_layout: Dict[str, str], 
    unigram_data: Dict[str, float], 
    trigram_data: Dict[str, float]
) -> Tuple[Dict[str, str], float, int]:
    """
    Spustí algoritmus Simulated Annealing (Simulované žíhání).
    """
    
    # definice povolených znaků
    swappable_chars = list(start_layout.keys())
    if ' ' in swappable_chars:
        swappable_chars.remove(' ') 
    
    current_layout = start_layout.copy()
    current_cost = calculate_total_cost(current_layout, unigram_data, trigram_data)
    best_layout = current_layout.copy()
    best_cost = current_cost
    
    T = T_START
    iteration = 0
    
    print(f"\n--- Spouštím Simulated Annealing ---")
    print(f"Startovní náklad: {current_cost:.4f}")
    print(f"Parametry: T_start={T_START}, T_end={T_END}, alpha={ALPHA}")

    while T > T_END:
        iteration += 1
        
        # výběr náhodného souseda
        new_layout = generate_random_neighbor(current_layout, swappable_chars)
        
        # výpočet nákladu nového řešení
        new_cost = calculate_total_cost(new_layout, unigram_data, trigram_data)
        
        # 3. Vyhodnocení
        cost_difference = new_cost - current_cost
        
        if cost_difference < 0:
            # řešení je LEPŠÍ (nižší náklad). Vždy je přijato.
            current_layout = new_layout
            current_cost = new_cost
            
            # aktualizace globálně nejlepšího řešení
            if current_cost < best_cost:
                best_cost = current_cost
                best_layout = current_layout.copy()
                print(f"Iter {iteration:8}: T={T:.6f}, Náklad={best_cost:.4f} (Nový rekord)")
                
        else:
            # řešení je HORŠÍ. Je přijato s pravděpodobností přijetí
            
            # pravděpodobnost přijetí (Boltzmannova distribuce)
            acceptance_prob = math.exp(-cost_difference / T)
            
            if random.random() < acceptance_prob:
                # přijme horší řešení
                current_layout = new_layout
                current_cost = new_cost
                
        # ochlazování
        T *= ALPHA
        
        # tisk stavu každých 10 000 iterací
        if iteration % 10000 == 0:
             print(f"Iter {iteration:8}: T={T:.6f}, Současný náklad={current_cost:.4f}")


    print(f"\n--- Simulated Annealing Hotovo ---")
    print(f"Celkový počet iterací: {iteration}")
    return best_layout, best_cost, iteration

# spuštění skriptu
if __name__ == "__main__":
    
    # spuštění SA
    sa_layout, sa_cost, sa_iter = simulated_annealing_optimize(
        start_layout=QWERTZ_LAYOUT, 
        unigram_data=UNIGRAM_DATA,
        trigram_data=TRIGRAM_DATA
    )
    
    print("\n-----------------------------------------------------")
    print("🎉 FINÁLNÍ VÝSLEDEK SIMULATED ANNEALING:")
    print(f"Optimální náklad: {sa_cost:.4f}")
    print(f"Celkový počet iterací: {sa_iter}")
    print("-----------------------------------------------------")

    # uložení výsledku SA
    with open("simulated_annealing_best_layout.json", "w", encoding="utf-8") as f:
        json.dump(sa_layout, f, indent=4, ensure_ascii=False)
        
    print(f"\n✅ Nejlepší SA rozložení uloženo do: simulated_annealing_best_layout.json")