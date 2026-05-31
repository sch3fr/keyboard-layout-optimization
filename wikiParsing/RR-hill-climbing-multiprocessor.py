# optimalizační algoritmus metodou Random Restart Hill CLimbing, využívá 
# multiprocessing
# POZOR spuštění využívá 100% CPU

import json
import random
import os
import time
from typing import Dict, List, Tuple
import concurrent.futures 

# import z cost_calculator
from cost_calculator import QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, calculate_total_cost 

# konfigurace maximálního počtu iterací a počtu restartování
MAX_ITERATIONS = 200 
NUM_RESTARTS = 50 

# generování sousedů
def get_all_neighbors(current_layout: Dict[str, str], swappable_chars: List[str]) -> List[Dict[str, str]]:
    neighbors = []
    n = len(swappable_chars)
    for i in range(n):
        for j in range(i + 1, n):
            char1 = swappable_chars[i]
            char2 = swappable_chars[j]
            new_layout = current_layout.copy()
            new_layout[char1] = current_layout[char2]
            new_layout[char2] = current_layout[char1]
            neighbors.append(new_layout)
    return neighbors

# hlavní algoritmus Hill Climbing
def hill_climbing_optimize(start_layout: Dict[str, str], unigram_data: Dict[str, float], trigram_data: Dict[str, float], swappable_chars: List[str], verbose: bool = True) -> Tuple[Dict[str, str], float, int]:
    current_layout = start_layout.copy()
    current_cost = calculate_total_cost(current_layout, unigram_data, trigram_data)
    
    if verbose:
        print(f"Startovní náklad: {current_cost:.4f}")

    iterations = 0
    while iterations < MAX_ITERATIONS:
        iterations += 1
        # generuje sousedy ze swappable_chars
        neighbors = get_all_neighbors(current_layout, swappable_chars)
        
        best_neighbor = None
        best_neighbor_cost = current_cost
        
        # hledá nejlepšího souseda (best choice)
        for neighbor_layout in neighbors:
            neighbor_cost = calculate_total_cost(neighbor_layout, unigram_data, trigram_data)
            if neighbor_cost < best_neighbor_cost:
                best_neighbor_cost = neighbor_cost
                best_neighbor = neighbor_layout
        
        # posun pokud našel lepší řešení
        if best_neighbor_cost < current_cost:
            current_layout = best_neighbor
            current_cost = best_neighbor_cost
            if verbose:
                print(f"Iterace {iterations:2}: Nový náklad = {current_cost:.4f}")
        else:
            break
            
    return current_layout, current_cost, iterations

# generování náhodného startu
def create_random_layout(base_layout: Dict[str, str]) -> Dict[str, str]:
    chars = list(base_layout.keys())
    positions = list(base_layout.values())
    random.shuffle(positions)
    return {char: pos for char, pos in zip(chars, positions)}

# WORKER FUNKCE PRO PARALELIZACI
def worker_task(args):
    """
    Tato funkce běží v samostatném procesu.
    Přijme jeden argument (tuple), rozbalí ho a spustí optimalizaci.
    """
    idx, initial_layout, unigram_data, trigram_data, swappable_chars = args
    
    # Každý proces si vygeneruje vlastní náhodný start
    # Poznámka: Random seed je v nových procesech řešen automaticky OS, 
    # ale pro jistotu lze zavolat random.seed() s unikátním ID, pokud by to dělalo problémy.
    start_layout = create_random_layout(initial_layout)
    
    final_layout, final_cost, iterations = hill_climbing_optimize(
        start_layout=start_layout,
        unigram_data=unigram_data,
        trigram_data=trigram_data,
        swappable_chars=swappable_chars,
        verbose=False # V paralelním běhu nechceme výpisy z každého kroku
    )
    
    return idx, final_layout, final_cost, iterations

# paralelní Random-Restart manager
def parallel_random_restart_hill_climbing(R: int, initial_layout: Dict[str, str], unigram_data: Dict[str, float], trigram_data: Dict[str, float]) -> Tuple[Dict[str, str], float]:
    
    # připravuje swappable chars
    swappable_chars = list(initial_layout.keys())
    if ' ' in swappable_chars:
        swappable_chars.remove(' ')

    # zjišťuje počet jader CPU
    cpu_cores = os.cpu_count() or 1
    print(f"\n--- Spouštím PARALELNÍ HC na {cpu_cores} jádrech (celkem {R} restartů) ---")
    
    best_overall_cost = float('inf')
    best_overall_layout = None

    # připravuje data pro workery
    # je potřeba vytvořit seznam úkolů. Každý úkol je tuple argumentů.
    tasks = []
    for i in range(R):
        tasks.append((i, initial_layout, unigram_data, trigram_data, swappable_chars))

    # ProcessPoolExecutor automaticky managuje procesy
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_cores) as executor:

        # as_completed umožňuje zpracovávat výsledky, jakmile doběhnou (v libovolném pořadí)
        future_to_id = {executor.submit(worker_task, task): task[0] for task in tasks}
        
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_id):
            idx, layout, cost, iters = future.result()
            completed_count += 1
            
            # jednoduchý progress bar
            print(f"\rDokončeno: {completed_count}/{R} (Poslední výsledek ID {idx}: {cost:.4f})", end="", flush=True)
            
            if cost < best_overall_cost:
                best_overall_cost = cost
                best_overall_layout = layout
                # vypisuje nový rekord na nový řádek, aby nezmizel
                print(f"\n[!] Nový globální rekord: {best_overall_cost:.4f} (v procesu {idx})")

    print(f"\n--- Paralelní výpočet dokončen ---")
    return best_overall_layout, best_overall_cost

# spuštění skriptu
if __name__ == "__main__":
    # Windows vyžaduje, aby kód spouštějící multiprocessing byl v bloku if __name__ == "__main__"
    
    start_time = time.time()
    
    swappable_chars = list(QWERTZ_LAYOUT.keys())
    if ' ' in swappable_chars:
        swappable_chars.remove(' ')
        
    print(f"Optimalizace klávesnice pro {NUM_RESTARTS} restartů.")
    
    best_layout, best_cost = parallel_random_restart_hill_climbing(
        R=NUM_RESTARTS,
        initial_layout=QWERTZ_LAYOUT,
        unigram_data=UNIGRAM_DATA,
        trigram_data=TRIGRAM_DATA
    )
    
    duration = time.time() - start_time
    
    print("\n-----------------------------------------------------")
    print("🎉 FINÁLNÍ SOUHRN VÝSLEDKŮ OPTIMALIZACE:")
    print(f"Baseline QWERTZ náklad: {calculate_total_cost(QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA):.4f}")
    print(f"Nejlepší nalezený náklad: {best_cost:.4f}")
    print(f"Čas výpočtu: {duration:.2f} sekund")
    print("-----------------------------------------------------")

    with open("parallel_best_layout.json", "w", encoding="utf-8") as f:
        json.dump(best_layout, f, indent=4, ensure_ascii=False)