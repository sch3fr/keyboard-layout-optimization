import xml.etree.ElementTree as ET
import re
import os
import json
from collections import Counter
from typing import Iterator, Dict

# --- DŮLEŽITÁ KONSTANTY ---
# Definice Jmenného prostoru (dle vzorku dumpu)
WIKI_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.11/}"

# Množina povolených znaků pro češtinu (+ mezery a základní interpunkce)
# Zahrň VŠECHNY znaky, které chceš umístit na klávesnici!
POVOLENE_ZNAKY = set("aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvyýzž.,!?():- /") 


# --- 1. XML EXTRACtion ---

def get_wiki_text_from_dump(dump_path: str) -> Iterator[str]:
    """
    Generátor, který efektivně prochází XML dump a vrací text článků.
    Obsahuje přesné hledání tagů a pojistku proti chybám NoneType.
    """
    for event, elem in ET.iterparse(dump_path, events=("end",)):
        
        if event == "end" and elem.tag == f'{WIKI_NAMESPACE}page':
            
            # 1. Extrakce elementů (ElementTree vrací None, pokud tag nenajde)
            title_elem = elem.find(f'{WIKI_NAMESPACE}title') 
            text_elem = elem.find(f'{WIKI_NAMESPACE}revision/{WIKI_NAMESPACE}text')
            ns_elem = elem.find(f'{WIKI_NAMESPACE}ns')
            
            # 2. **NEPRŮSTŘELNÁ KONTROLA TEXTU A TITULKU:**
            # Zajišťuje, že proměnné title, wiki_text a ns_val jsou vždy STRING (ne None).
            title = title_elem.text if title_elem is not None and title_elem.text is not None else ""
            
            # KLÍČOVÁ ZMĚNA: Kontrolujeme existenci text_elem a text_elem.text
            wiki_text = text_elem.text if text_elem is not None and text_elem.text is not None else ""
            
            ns_val = ns_elem.text if ns_elem is not None and ns_elem.text is not None else "-1"
            
            # --- ZPŘÍSNĚNÁ FILTRACE ---

            is_technical_title = title.startswith("Portál") or \
                                 title.startswith("Wikipedie") or \
                                 title.startswith("Šablona") or \
                                 title.startswith("Nápověda")
            
            # Zde už je volání .strip() BEZPEČNÉ, protože wiki_text je garantovaně STRING.
            is_main_namespace = ns_val == '0'
            is_valid_title = ':' not in title
            is_long_enough = len(wiki_text.strip()) > 100 
            is_redirect = wiki_text.strip().lower().startswith('#redirect')

            if wiki_text and is_main_namespace and is_valid_title and is_long_enough and not is_redirect: 
                yield wiki_text
            
            elem.clear()

            
# --- 2. MEDIAWIKI MARKUP CLEANING ---

"""
def clean_wiki_markup(wiki_text: str) -> str:

    #Odstraní MediaWiki formátování, šablony, reference a externí odkazy. Text je připraven pro další filtraci povolených českých znaků.

    if not wiki_text:
        return ""
    
    # 1. Odstranění HTML/XML tagů (např. <ref>...</ref>)
    # Používáme re.DOTALL, protože tagy mohou být na více řádcích
    text = re.sub(r'<ref.*?<\/ref>', '', wiki_text, flags=re.DOTALL)
    # Odstranění obecných HTML/XML tagů (např. <div...>, <span...>)
    text = re.sub(r'<[^>]+>', '', text, flags=re.DOTALL)
    
    # 2. Odstranění komentářů
    text = re.sub(r'', '', text, flags=re.DOTALL)
    
    # 3. Odstranění šablon {{...}}
    # Zvýšeno na 10 opakování, aby se odstranily i hluboce vnořené navigační prvky.
    for _ in range(10): 
        text = re.sub(r'\{\{[^\{\}]*?\}\}', '', text, flags=re.DOTALL)

    # 4. Odstranění odkazů na Soubory/Obrázky (např. [[Soubor:Název|popisek]])
    text = re.sub(r'\[\[(Soubor|File|Obrázek):.*?\]\]', '', text, flags=re.IGNORECASE)
    
    # 5. Odstranění externích odkazů (např. [http://url Popis] -> necháme Popis, pokud existuje)
    text = re.sub(r'\[http[s]?://[^\s]*?\s?([^\]]*)\]', r'\1', text)
    
    # 6. Odstranění tučného/kurzívy ('')
    text = re.sub(r'\'{2,5}', '', text)

    # 7. Zpracování Wiki odkazů
    # [[Cíl|Popis]] -> zachováme Popis
    text = re.sub(r'\[\[[^\|]*?\|([^\|]*?)\]\]', r'\1', text) 
    # [[Cíl]] -> zachováme Cíl
    text = re.sub(r'\[\[([^\]]*?)\]\]', r'\1', text) 

    # 8. Odstranění nadpisů (== Nadpis ==) a vodorovných čar
    text = re.sub(r'^=+\s*.*?\s*=+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^-+$', '', text, flags=re.MULTILINE)

    # 9. Normalizace mezer a nových řádků
    # Nahradíme všechny nové řádky mezerami
    text = re.sub(r'\n+', ' ', text)
    # Odstraníme vícenásobné mezery a mezery na začátku/konci
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    return text
"""
def clean_wiki_markup(wiki_text: str) -> str:
    if not wiki_text:
        return ""
    
    # 1. Odstranění HTML/XML tagů a referencí (agresivně)
    text = re.sub(r'<ref.*?<\/ref>', '', wiki_text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text, flags=re.DOTALL)
    
    # 2. Odstranění komentářů a šablon (včetně vnořených, 10 opakování)
    text = re.sub(r'', '', text, flags=re.DOTALL)
    for _ in range(10): 
        text = re.sub(r'\{\{[^\{\}]*?\}\}', '', text, flags=re.DOTALL)

    # 3. Odstranění wiki odkazů a externích odkazů (Největší zdroj znečištění)
    # Odstraňuje [[Cíl|Popis]] a [[Cíl]] bez zachování textu, protože tam může být šum!
    text = re.sub(r'\[\[.*?\]\]', '', text)
    text = re.sub(r'\[http[s]?://.*?\]', '', text) 
    
    # 4. Odstranění formátování obrázků, souborů a kategorizačních tagů
    text = re.sub(r'\[\[(Soubor|File|Obrázek|Kategorie):.*?\]\]', '', text, flags=re.IGNORECASE)
    
    # 5. Odstranění tučného/kurzívy ('')
    text = re.sub(r'\'{2,5}', '', text)
    
    # 6. Normalizace mezer a nových řádků
    text = re.sub(r'={2,}\s*.*?\s*={2,}', '', text) # Nadpisy
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    return text
# --- 3. DIGRAM COUNTING ON THE FLY ---

def spocitej_digramy_on_the_fly(text: str, counter: Counter):
    """Aktualizuje Counter pro digramy."""
    for i in range(len(text) - 1):
        counter[text[i:i+2]] += 1

def process_and_analyze_dump(dump_path: str) -> Dict[str, float]:
    """
    Hlavní funkce, která zpracovává dump a počítá digramy on-the-fly.
    """
    digram_counter = Counter()
    clanok_count = 0
    celkova_delka_korpusu = 0
    
    text_generator = get_wiki_text_from_dump(dump_path)
    
    # --- CYKLUS PRO ZPRACOVÁNÍ DAT (BEZ TQDM) ---
    print("Zpracování článků začalo. Může trvat dlouho, prosím čekejte...")
    
    for wiki_text in text_generator:
        
        clanok_count += 1
        
        # Tisknutí stavu každých 10 000 článků (jednoduchý progress)
        if clanok_count % 10000 == 0:
            print(f"   [INFO] Zpracováno článků: {clanok_count:,}. Délka korpusu: {celkova_delka_korpusu:,} znaků.")
        
        # Čištění a filtrace
        clean_text = clean_wiki_markup(wiki_text).lower()
        final_text = "".join(char for char in clean_text if char in POVOLENE_ZNAKY or char == ' ')
        
        # Počítání digramů
        spocitej_digramy_on_the_fly(final_text, digram_counter)
        
        celkova_delka_korpusu += len(final_text)

    # Přepočet absolutních počtů na relativní frekvenci
    celkovy_pocet_digramu = sum(digram_counter.values())
    
    if celkovy_pocet_digramu == 0:
        return {}

    relativni_frekvence = {digram: pocet / celkovy_pocet_digramu 
                            for digram, pocet in digram_counter.items()}
    
    print(f"   [INFO] Hotovo! Celkový počet zpracovaných článků: {clanok_count:,}. Celková délka korpusu: {celkova_delka_korpusu:,} znaků.")
    
    return relativni_frekvence

# --- 4. EXECUTION ---

if __name__ == "__main__":
    DUMP_CEST = "cswiki-latest-pages-articles.xml"  
    
    if not os.path.exists(DUMP_CEST):
        print("🛑 CHYBA: Soubor dumpu nebyl nalezen na zadané cestě.")
        print(f"Cesta: {DUMP_CEST}")
        exit()

    print(f"✅ Spouštím sběr dat z dumpu: {DUMP_CEST}")

    # Zpracování a výpočet frekvencí
    frekvence_digramu = process_and_analyze_dump(DUMP_CEST)

    if frekvence_digramu:
        # Uložení frekvencí do JSON
        try:
            relevantni_digramy = {k: v for k, v in frekvence_digramu.items() if v > 0.00001} 
            
            with open("frekvence_digramu_cs.json", "w", encoding="utf-8") as f:
                json.dump(relevantni_digramy, f, ensure_ascii=False, indent=4)
                
            print(f"🎉 ÚSPĚCH: Frekvence digramů uložena do 'frekvence_digramu_cs.json'.")
            print(f"Počet relevantních digramů: {len(relevantni_digramy)}.")
            
        except Exception as e:
            print(f"🛑 CHYBA PŘI UKLÁDÁNÍ JSON: {e}")