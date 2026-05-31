import json
from typing import Dict

# Importuje data
from cost_calculator import (
    QWERTZ_LAYOUT, UNIGRAM_DATA, ANATOMY_MAP
)

def calculate_finger_load(layout: Dict[str, str], title: str):
    # 1. Výpočet celkového počtu znaků (BEZ MEZERY, aby to dalo 100 %)
    total_unigrams = sum(freq for char, freq in UNIGRAM_DATA.items() if char != ' ')
    
    finger_loads = {}
    hand_loads = {'Left': 0.0, 'Right': 0.0}
    row_loads = {}
    
    # 2. Procházení layoutu a sčítání zátěže
    for char, pos in layout.items():
        if char == ' ':
            continue
            
        freq = UNIGRAM_DATA.get(char, 0)
        rel_freq = (freq / total_unigrams) * 100  # Převod na procenta
        
        if pos in ANATOMY_MAP:
            anatomy_info = ANATOMY_MAP[pos]
            
            try:
                ruka = anatomy_info[0] # např. 'L' nebo 'P'
                prst = anatomy_info[1] # např. 'I', 'M'
                rada = anatomy_info[2] # Získání řady (např. 'Home', 'Top', 'Bottom')
                
                # Zápis prstů
                finger_key = f"{ruka}_{prst}"
                finger_loads[finger_key] = finger_loads.get(finger_key, 0.0) + rel_freq
                
                # Zápis řad
                row_loads[rada] = row_loads.get(rada, 0.0) + rel_freq
                
                # Zápis rukou (opraveno i pro české 'P')
                if 'L' in str(ruka).upper():
                    hand_loads['Left'] += rel_freq
                elif 'P' in str(ruka).upper() or 'R' in str(ruka).upper():
                    hand_loads['Right'] += rel_freq
                    
            except IndexError:
                # Fallback, pokud by v ANATOMY_MAP chyběla řada nebo ruka
                prst = str(anatomy_info)
                finger_loads[prst] = finger_loads.get(prst, 0.0) + rel_freq
    
    # 3. Vykreslení výsledků
    print(f"\n{'='*40}")
    print(f" ANALÝZA: {title.upper()}")
    print(f"{'='*40}")
    
    # Vykreslení zátěže prstů
    print("--- Zátěž prstů ---")
    for finger, load in sorted(finger_loads.items()):
        bar_length = int(load)
        bar = '█' * bar_length
        print(f"{finger:<15} | {load:5.2f}% | {bar}")
        
    print(f"\nZátěž rukou: LEVÁ = {hand_loads['Left']:.1f}% | PRAVÁ = {hand_loads['Right']:.1f}%")
    
    # Vykreslení zátěže řad
    print("\n--- Zátěž řad ---")
    # Můžeme seřadit podle zátěže sestupně
    for row, load in sorted(row_loads.items(), key=lambda item: item[1], reverse=True):
        bar_length = int(load)
        bar = '█' * bar_length
        print(f"{row:<15} | {load:5.2f}% | {bar}")
        
if __name__ == "__main__":
    # 1. Analýza původní QWERTZ
    calculate_finger_load(QWERTZ_LAYOUT, "Základní QWERTZ")
    
    # 2. Pokus o načtení nejlepšího vygenerovaného layoutu
    # Změň název souboru podle toho, který algoritmus dopadl nejlépe
    try:
        with open("ga_best_layout.json", "r", encoding="utf-8") as f:
            custom_layout = json.load(f)
        calculate_finger_load(custom_layout, "Optimalizovaná Klávesnice (GA)")
    except FileNotFoundError:
        print("\n[!] Soubor 'ga_best_layout.json' nebyl nalezen. Pokud chceš analyzovat svůj layout, uprav název souboru ve skriptu.")