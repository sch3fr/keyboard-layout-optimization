import json
import random
import copy
from typing import Dict, List, Tuple

# Importuje počítadlo nákladu
from cost_calculator import (
    QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, 
    calculate_total_cost, ANATOMY_MAP
)

# --- Hyperparametry Genetického Algoritmu ---
POPULATION_SIZE = 50    # Velikost populace (počet klávesnic v jedné generaci)
GENERATIONS = 100       # Počet generací
MUTATION_RATE = 0.15    # Šance, že dítě zmutuje (náhodně prohodí 2 klávesy)
TOURNAMENT_SIZE = 5     # Kolik jedinců soupeří o to, stát se rodičem
ELITISM = 2             # Kolik nejlepších jedinců automaticky přechází do další generace

# --- Pomocné funkce ---

def quick_local_search(layout: Dict[str, str], chars_to_swap: List[str], max_steps: int = 20):
    """Hybridizace: Učeše dítě po narození a mutaci."""
    current_layout = layout.copy()
    current_cost = calculate_total_cost(current_layout, UNIGRAM_DATA, TRIGRAM_DATA)
    
    for _ in range(max_steps):
        c1, c2 = random.sample(chars_to_swap, 2)
        test_layout = current_layout.copy()
        test_layout[c1], test_layout[c2] = test_layout[c2], test_layout[c1]
        
        new_cost = calculate_total_cost(test_layout, UNIGRAM_DATA, TRIGRAM_DATA)
        if new_cost < current_cost:
            current_cost = new_cost
            current_layout = test_layout
            
    return current_layout, current_cost

def order_crossover(parent1: Dict[str, str], parent2: Dict[str, str], chars: List[str]) -> Dict[str, str]:
    """
    Speciální křížení pro permutace (Order Crossover).
    Zajistí, že dítě bude mít všechny znaky právě jednou.
    """
    size = len(chars)
    # Vybere náhodný výsek (začátek a konec)
    start, end = sorted(random.sample(range(size), 2))
    
    child_layout = {}
    # Uchovává si pozice, které už jsou obsadili
    used_positions = set()
    
    # 1. Krok: Zkopíruje výsek z Rodiče 1
    for i in range(start, end):
        char = chars[i]
        pos = parent1[char]
        child_layout[char] = pos
        used_positions.add(pos)
        
    # 2. Krok: Doplní zbytek z Rodiče 2
    # Prochází znaky, které ještě nejsou v child_layout
    remaining_chars = [c for c in chars if c not in child_layout]
    
    # Prochází pozice z Rodiče 2 v pořadí
    p2_positions = [parent2[c] for c in chars]
    
    char_idx = 0
    for pos in p2_positions:
        if pos not in used_positions:
            # Vezme další volný znak a přiřadí mu tuto pozici z Rodiče 2
            if char_idx < len(remaining_chars):
                child_layout[remaining_chars[char_idx]] = pos
                char_idx += 1
                
    # Pro jistotu zkopíruje mezeru (ta se nekříží)
    child_layout[' '] = parent1.get(' ', 'KEY_SPACE')
    
    return child_layout

def mutate(layout: Dict[str, str], chars: List[str]) -> Dict[str, str]:
    """Mutace: Náhodně prohodí dvě klávesy."""
    new_layout = layout.copy()
    c1, c2 = random.sample(chars, 2)
    new_layout[c1], new_layout[c2] = new_layout[c2], new_layout[c1]
    return new_layout

def tournament_selection(population: List[Tuple[Dict, float]]) -> Dict[str, str]:
    """Vybere náhodnou skupinku a z ní vybere toho nejlepšího rodiče."""
    tournament = random.sample(population, TOURNAMENT_SIZE)
    # Population je seznam n-tic: (layout, cost)
    best_parent = min(tournament, key=lambda x: x[1])
    return best_parent[0]

# --- Hlavní Genetický Algoritmus ---

def ga_optimize():
    swappable_chars = [c for c in QWERTZ_LAYOUT.keys() if c != ' ']
    space_char = ' '
    space_pos = QWERTZ_LAYOUT.get(' ', 'KEY_SPACE')
    all_positions = [v for k, v in QWERTZ_LAYOUT.items() if k != ' ']
    
    print(f"--- Spouštím Genetický Algoritmus ({POPULATION_SIZE} jedinců) ---")
    
    # 1. Inicializace první generace
    population = []
    for _ in range(POPULATION_SIZE):
        layout = QWERTZ_LAYOUT.copy()
        random.shuffle(all_positions)
        for i, char in enumerate(swappable_chars):
            layout[char] = all_positions[i]
        layout[space_char] = space_pos
        
        # Rovnou hybridizuje startovní populaci, ať vznikne dobrý základ
        layout, cost = quick_local_search(layout, swappable_chars, max_steps=10)
        population.append((layout, cost))
        
    # Seřadím populaci od nejlepšího (nejnižší cost) po nejhorší
    population.sort(key=lambda x: x[1])
    global_best_layout = population[0][0]
    global_best_cost = population[0][1]
    
    print(f"Startovní nejlepší náklad: {global_best_cost:.4f}")

    # 2. Evoluční cyklus
    for gen in range(GENERATIONS):
        new_population = []
        
        # Elitismus: Zachová pár nejlepších nezměněných
        for i in range(ELITISM):
            new_population.append(population[i])
            
        # Vytvoří zbytek nové generace
        while len(new_population) < POPULATION_SIZE:
            # Výběr rodičů
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)
            
            # Křížení
            child = order_crossover(parent1, parent2, swappable_chars)
            
            # Mutace
            if random.random() < MUTATION_RATE:
                child = mutate(child, swappable_chars)
                
            # Hybridizace (Memetický prvek)
            child, cost = quick_local_search(child, swappable_chars, max_steps=20)
            
            new_population.append((child, cost))
            
        # Zhodnocení nové generace a seřazení
        population = new_population
        population.sort(key=lambda x: x[1])
        
        # Kontrola rekordu
        current_best_cost = population[0][1]
        if current_best_cost < global_best_cost:
            global_best_cost = current_best_cost
            global_best_layout = population[0][0]
            print(f"Gen {gen+1:3}: 🧬 Nový rekord: {global_best_cost:.4f}")

    return global_best_layout, global_best_cost

if __name__ == "__main__":
    try:
        best_layout, best_cost = ga_optimize()
        print(f"\n✅ Genetický Algoritmus dokončen.")
        print(f"🏆 NEJLEPŠÍ NÁKLAD: {best_cost:.4f}")
        
        with open("ga_best_layout.json", "w", encoding="utf-8") as f:
            json.dump(best_layout, f, indent=4, ensure_ascii=False)
            print("Výsledek uložen do 'ga_best_layout.json'.")
            
    except Exception as e:
        print(f"\n❌ Chyba: {e}")