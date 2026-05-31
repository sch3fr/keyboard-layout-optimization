import json
from typing import Dict, Tuple

# 1. ANATOMICKÁ MAPA KLÁVESNICE

# Definice anatomické mapy (Ruka, Prst, Řada) pro standardní QWERTZ klávesy
# Ruka: L=Levá, P=Pravá, T=Palec (pro mezeru)
# Prst: I=Ukazováček, M=Prostředníček, R=Prsteníček, P=Malíček, T=Palec
# Řada: N=Číselná/Diakritika, H=Horní, M=Střední/Home, D=Dolní, E=Extrémní (mezera)

"""
    Hlavní skript pro výpočet nákladové funkce. V základu počítá hodnotu 
    nákladové funkce pro QWERTZ rozložení klávesnice, a ostatní skripty
    jej využívají pro porovnání nových rozložení 
"""

ANATOMY_MAP = {
    # Levá ruka - Číselná/Diakritika (N)
    'KEY_2': ('L', 'R', 'N'), 'KEY_3': ('L', 'M', 'N'), #'KEY_1': ('L', 'P', 'N') vyřazeno, protože na qwertz není znak české abecedy
    'KEY_4': ('L', 'I', 'N'), 'KEY_5': ('L', 'I', 'N'), 
    # Levá ruka - Horní řada (H)
    'KEY_Q': ('L', 'P', 'H'), 'KEY_W': ('L', 'R', 'H'), 'KEY_E': ('L', 'M', 'H'),
    'KEY_R': ('L', 'I', 'H'), 'KEY_T': ('L', 'I', 'H'), 
    # Levá ruka - Home Row (M)
    'KEY_A': ('L', 'P', 'M'), 'KEY_S': ('L', 'R', 'M'), 'KEY_D': ('L', 'M', 'M'),
    'KEY_F': ('L', 'I', 'M'), 'KEY_G': ('L', 'I', 'M'), 
    # Levá ruka - Dolní řada (D)
    'KEY_Z': ('L', 'P', 'D'), 'KEY_X': ('L', 'R', 'D'), 'KEY_C': ('L', 'M', 'D'),
    'KEY_V': ('L', 'I', 'D'), 'KEY_B': ('L', 'I', 'D'),

    # Pravá ruka - Číselná/Diakritika (N)
    'KEY_6': ('P', 'I', 'N'), 'KEY_7': ('P', 'I', 'N'), 'KEY_8': ('P', 'M', 'N'),
    'KEY_9': ('P', 'R', 'N'), 'KEY_0': ('P', 'P', 'N'), 
    # Pravá ruka - Horní řada (H)
    'KEY_Y': ('P', 'I', 'H'),'KEY_U': ('P', 'I', 'H'), 'KEY_I': ('P', 'M', 'H'), 'KEY_O': ('P', 'R', 'H'),
    'KEY_P': ('P', 'P', 'H'), 'KEY_SLASH': ('P', 'P', 'H'), #KEY_SLASH je  na qwertz 'ú' a '/'
    # Pravá ruka - Home Row (M)
    'KEY_H': ('P', 'I', 'M'), 'KEY_J': ('P', 'I', 'M'), 'KEY_K': ('P', 'M', 'M'), 
    'KEY_L': ('P', 'R', 'M'), 'KEY_SEMI': ('P', 'P', 'M'), #KEY_SEMI je na qwertz 'ů' a horní uvozovky
    # Pravá ruka - Dolní řada (D)
    'KEY_N': ('P', 'I', 'D'), 'KEY_M': ('P', 'M', 'D'), 'KEY_COMMA': ('P', 'R', 'D'),
    'KEY_DOT': ('P', 'P', 'D'), #'KEY_DASH': ('P', 'P', 'D'),
    
    # Speciální
    'KEY_SPACE': ('T', 'T', 'E'), # Palec, Extrémní řada
}

# 2. HODNOTY NÁKLADU A VÁHY 

# A. Náklad polohy (Unigram Cost)
POSITIONAL_COSTS = {
    'M': {'I': 1.0, 'M': 1.1, 'R': 1.5, 'P': 2.0, 'T': float('inf')}, # Home Row
    'H': {'I': 1.8, 'M': 2.0, 'R': 2.2, 'P': 3.0, 'T': float('inf')}, # Horní řada
    'D': {'I': 2.5, 'M': 2.8, 'R': 3.5, 'P': 4.5, 'T': float('inf')}, # Dolní řada
    'N': {'I': 3.0, 'M': 3.5, 'R': 4.0, 'P': 5.0, 'T': float('inf')}, # Číselná/Diakritika
    'E': {'T': 1.0, 'I': 5.0, 'M': 5.0, 'R': 5.0, 'P': 5.0}, # Mezera/Extrémní (jen palec levný)
}

# B. Váhy pro kombinovanou Cost Function (Důraz na sekvenci)
ALPHA = 0.2  # Váha pro Unigram Cost (Poloha)
GAMMA = 0.8  # Váha pro Trigram Cost (Sekvence)

# --- 3. FUNKCE VÝPOČTU NÁKLADŮ ---

def get_unigram_cost(current_layout: Dict[str, str], unigram_frequencies: Dict[str, float]) -> float:
    """Vypočítá celkový náklad polohy (Unigram Cost)."""
    total_cost = 0.0
    
    for char, freq in unigram_frequencies.items():
        if len(char) == 1:
            try:
                key_pos_name = current_layout[char]
                ruka, prst, rada = ANATOMY_MAP[key_pos_name]
                cost_value = POSITIONAL_COSTS[rada][prst]
                total_cost += freq * cost_value
            except KeyError:
                continue
                
    return total_cost

def get_trigram_cost(pos_1: Tuple, pos_2: Tuple, pos_3: Tuple) -> float:
    """Určí náklad (Cost) pro sekvenci tří úhozů A -> B -> C."""
    
    ruka_1, prst_1, rada_1 = pos_1
    ruka_2, prst_2, rada_2 = pos_2
    ruka_3, prst_3, rada_3 = pos_3
    
    # --- 1. Základní Trigram Cost (Sekvenční obtížnost) ---
    
    if prst_1 == prst_2 and prst_2 == prst_3 and prst_1 != 'T':
        base_cost = 15.0 # Smyk
    elif ruka_1 != ruka_2 and ruka_2 != ruka_3 and ruka_1 == ruka_3 and ruka_1 != 'T' and ruka_2 != 'T':
        base_cost = 1.0 # Plné střídání rukou
    elif prst_1 == prst_2 or prst_2 == prst_3:
        base_cost = 8.0 # Hop
    elif ruka_1 == ruka_2 and ruka_2 == ruka_3:
        base_cost = 4.5 # Monotónnost
    else:
        base_cost = 3.0 # Základní střídání prstů/rukou
        
    # --- 2. Dodatečná penalizace za skok na N-řadu ---
    
    extra_penalty = 0.0
    for r1, r2 in [(rada_1, rada_2), (rada_2, rada_3)]:
        if (r1 == 'N' and r2 in ('M', 'H')) or (r1 in ('M', 'H') and r2 == 'N'):
            extra_penalty += 2.0
        
    return base_cost + extra_penalty


def calculate_total_cost(current_layout: Dict[str, str], unigram_data: Dict[str, float], trigram_data: Dict[str, float]) -> float:
    """Vypočítá celkový vážený náklad rozložení (Unigram + Trigram)."""
    
    # 1. počítá Unigram Cost (Poloha)
    unigram_cost = get_unigram_cost(current_layout, unigram_data)
    
    # 2. počítá Trigram Cost (Sekvence)
    trigram_cost = 0.0
    
    for sequence, freq in trigram_data.items():
        if len(sequence) == 3:
            char_1, char_2, char_3 = sequence[0], sequence[1], sequence[2]
            
            try:
                pos_1 = ANATOMY_MAP[current_layout[char_1]]
                pos_2 = ANATOMY_MAP[current_layout[char_2]]
                pos_3 = ANATOMY_MAP[current_layout[char_3]]
                
                cost_value = get_trigram_cost(pos_1, pos_2, pos_3)
                trigram_cost += freq * cost_value
                
            except KeyError:
                continue

    total_cost = (ALPHA * unigram_cost) + (GAMMA * trigram_cost)
    return total_cost

# 4. DATA A VÝCHOZÍ ROZLOŽENÍ (Zveřejněno pro import)

# výchozí rozložení (QWERTZ)
QWERTZ_LAYOUT = {
    'q': 'KEY_Q', 'w': 'KEY_W', 'e': 'KEY_E', 'r': 'KEY_R', 't': 'KEY_T',
    'z': 'KEY_Z', 'u': 'KEY_U', 'i': 'KEY_I', 'o': 'KEY_O', 'p': 'KEY_P', 'ú': 'KEY_SLASH',
    'a': 'KEY_A', 's': 'KEY_S', 'd': 'KEY_D', 'f': 'KEY_F', 'g': 'KEY_G',
    'h': 'KEY_H', 'j': 'KEY_J', 'k': 'KEY_K', 'l': 'KEY_L', 'ů': 'KEY_SEMI',
    'y': 'KEY_Y', 'x': 'KEY_X', 'c': 'KEY_C', 'v': 'KEY_V', 'b': 'KEY_B',
    'n': 'KEY_N', 'm': 'KEY_M', ',': 'KEY_COMMA', '.': 'KEY_DOT',
    
    # Diakritika
    'ě': 'KEY_2', 'š': 'KEY_3', 'č': 'KEY_4', 'ř': 'KEY_5', 'ž': 'KEY_6',
    'ý': 'KEY_7', 'á': 'KEY_8', 'í': 'KEY_9', 'é': 'KEY_0', 
    
    # Mezera
    ' ': 'KEY_SPACE' 
}

try:
    with open("frekvence_unigramu_cs.json", "r", encoding="utf-8") as f:
        UNIGRAM_DATA = json.load(f)
    with open("frekvence_trigramu_cs.json", "r", encoding="utf-8") as f:
        TRIGRAM_DATA = json.load(f)
except FileNotFoundError:
    print("UPOZORNĚNÍ: Frekvenční data nejsou načtena v cost_calculator.py!")
    UNIGRAM_DATA = {}
    TRIGRAM_DATA = {}

if __name__ == "__main__":
    cost_qwertz = calculate_total_cost(QWERTZ_LAYOUT, UNIGRAM_DATA, TRIGRAM_DATA)
    print(f"\n✅ Samotest Cost Function (QWERTZ): {cost_qwertz:.4f}")