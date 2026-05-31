# Tento skript pouze řadí výstupy n-gramové analýzy, pro potřeby samostatné
# práce irelevantní

import json
import os
import sys


# definice vstupních souborů
files = {
    "1": "frekvence_unigramu_cs_raw.json",
    "2": "frekvence_digramu_cs_raw.json",
    "3": "frekvence_trigramu_cs_raw.json"
}

print("--- Řazení N-gramů ---")
print("Který soubor seřadit?")
for key, filename in files.items():
    print(f"[{key}] {filename}")

# vstup uživatele
choice = input("\nVyberte číslo (1-3): ").strip()

if choice not in files:
    print("Neplatná volba, proces končí.")
    sys.exit()

input_file = files[choice]

# generování výstupního souboru
# mění např. "frekvence_unigramu_cs_raw.json" into "frekvence_unigramu_cs_sorted.json"
output_file = input_file.replace("raw.json", "sorted.json")

# logika řazení
try:
    # načítání json
    print(f"Zpracovávám: {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # key=lambda x: x[1] cílí na hodnotu čísla
    # reverse = true řadí sestupně
    sorted_data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))

    # zápis do nového souboru
    print(f"Ukládám do:  {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # ensure_ascii=False zajišťuje propis znaků s diakritikou
        json.dump(sorted_data, f, indent=4, ensure_ascii=False)

    print("Hotovo! ✅")

# ochrana chyb
except FileNotFoundError:
    print(f"Chyba: Soubor '{input_file}' nebyl nalezen v tomto adresáři.")
except json.JSONDecodeError:
    print(f"Chyba: Soubor '{input_file}' není validní JSON.")