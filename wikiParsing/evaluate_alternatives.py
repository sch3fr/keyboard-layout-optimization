import json
from cost_calculator import (
    QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA, calculate_total_cost
)

def create_layout_from_mapping(base_layout, mapping):
    """
    Vytvoří nový layout tím, že přeskládá znaky na fyzické pozice
    existující klávesnice (podle referenčního mapování).
    """
    new_layout = base_layout.copy()
    
    # Prohodíme písmena podle definice.
    for new_char, qwertz_equivalent in mapping.items():
        if qwertz_equivalent in base_layout:
            new_layout[new_char] = base_layout[qwertz_equivalent]
            
    return new_layout

# --- MAPOVÁNÍ: COLEMAK ---
# Čte se to: "Písmeno 'f' v Colemaku leží na fyzické klávese, kde má QWERTZ 'e'."
colemak_map = {
    'q': 'q', 'w': 'w', 'f': 'e', 'p': 'r', 'g': 't', 'j': 'z', 'l': 'u', 'u': 'i', 'y': 'o',
    'a': 'a', 'r': 's', 's': 'd', 't': 'f', 'd': 'g', 'h': 'h', 'n': 'j', 'e': 'k', 'i': 'l', 'o': 'ů',
    'z': 'y', 'x': 'x', 'c': 'c', 'v': 'v', 'b': 'b', 'k': 'n', 'm': 'm'
}

# --- MAPOVÁNÍ: DVORAK ---
dvorak_map = {
    'p': 'r', 'y': 't', 'f': 'z', 'g': 'u', 'c': 'i', 'r': 'o', 'l': 'p',
    'a': 'a', 'o': 's', 'e': 'd', 'u': 'f', 'i': 'g', 'd': 'h', 'h': 'j', 't': 'k', 'n': 'l', 's': 'ů',
    'q': 'x', 'j': 'c', 'k': 'v', 'x': 'b', 'b': 'n', 'm': 'm', 'w': ',', 'v': '.', 'z': '-'
}

def compare_layouts():
    print(f"{'='*50}")
    print(" SOUBOJ KLÁVESNIC: QWERTZ vs COLEMAK vs DVORAK")
    print(f"{'='*50}\n")

    # 1. QWERTZ (Základní referenční bod)
    qwertz_cost = calculate_total_cost(QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA)
    print(f"1. Standardní QWERTZ:       {qwertz_cost:.4f}")

    # 2. Colemak
    colemak_layout = create_layout_from_mapping(QWERTZ_LAYOUT, colemak_map)
    colemak_cost = calculate_total_cost(colemak_layout, UNIGRAM_DATA, TRIGRAM_DATA)
    print(f"2. Colemak (Anglický):      {colemak_cost:.4f}")

    # 3. Dvorak
    dvorak_layout = create_layout_from_mapping(QWERTZ_LAYOUT, dvorak_map)
    dvorak_cost = calculate_total_cost(dvorak_layout, UNIGRAM_DATA, TRIGRAM_DATA)
    print(f"3. Dvorak (Anglický):       {dvorak_cost:.4f}")

    # 4. Tvé vlastní SA řešení (Pokusí se načíst, pokud existuje)
    try:
        with open("ga_best_layout_FIN.json", "r", encoding="utf-8") as f:
            sa_layout = json.load(f)
        sa_cost = calculate_total_cost(sa_layout, UNIGRAM_DATA, TRIGRAM_DATA)
        print(f"\n🏆 Tvoje SA Klávesnice:      {sa_cost:.4f}")
        
        # Malé srovnání
        diff = ((qwertz_cost - sa_cost) / qwertz_cost) * 100
        print(f"   -> O {diff:.1f}% efektivnější než QWERTZ!")
        
    except FileNotFoundError:
        print("\n[!] Soubor 'sa_best_layout.json' nebyl nalezen. Přidej ho pro srovnání.")

if __name__ == "__main__":
    compare_layouts()