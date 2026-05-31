import xml.etree.ElementTree as ET
import re
import os
import json
from collections import Counter
from typing import Iterator, Dict

# Namespace pro MediaWiki dumpy (nutné pro správné hledání elementů)
# WIKI_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.10/}"

# --- 1. XML EXTRACtion ---

import xml.etree.ElementTree as ET
# ... ostatní importy ...
import xml.etree.ElementTree as ET
# ... ostatní importy ...

# --- NOVÝ A OPRAVENÝ NAMESPACE ---
# Extrahováno ze vzorku: xmlns="http://www.mediawiki.org/xml/export-0.11/" 
WIKI_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.11/}" 


def get_wiki_text_from_dump(dump_path: str) -> Iterator[str]:
    """
    Generátor, který efektivně prochází XML dump.
    Používá explicitní jmenný prostor pro přesné nalezení obsahu.
    """
    
    # Použití iterparse pro streamování
    for event, elem in ET.iterparse(dump_path, events=("end",)):
        
        # Hledá tag 'page' s explicitním jmenným prostorem
        if event == "end" and elem.tag == f'{WIKI_NAMESPACE}page':
            
            # Hledání v rámci aktuální 'page' s použitím JMENNÉHO PROSTORU
            title_elem = elem.find(f'{WIKI_NAMESPACE}title') 
            
            # Text je vnořen: revision/text
            text_elem = elem.find(f'{WIKI_NAMESPACE}revision/{WIKI_NAMESPACE}text')

            title = title_elem.text if title_elem is not None else ""
            wiki_text = text_elem.text if text_elem is not None else ""
            
            # Filtrování: Vynechat technické stránky (ns=0 jsou články, ostatní jsou diskuze/šablony)
            # Navíc ověří, že v titulku není dvojtečka, abychom vyřadili Soubor:, Kategorie: atd. [cite: 2, 3]
            ns_elem = elem.find(f'{WIKI_NAMESPACE}ns')
            ns_val = ns_elem.text if ns_elem is not None else "-1"
            
            if wiki_text and ns_val == '0' and ':' not in title: 
                yield wiki_text
            
            # Vyčištění elementu z paměti
            elem.clear()


# --- 2. MediaWiki Makrup čištění ---

def clean_wiki_markup(wiki_text: str) -> str:
    """
    Odstraní MediaWiki formátování, šablony, reference a externí odkazy pomocí RegEx.
    """
    if not wiki_text:
        return ""
    
    # 1. Odstranění HTML/XML tagů (např. <ref>...</ref> a obecných tagů)
    text = re.sub(r'<ref.*?<\/ref>', '', wiki_text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text, flags=re.DOTALL)
    
    # 2. Odstranění komentářů
    text = re.sub(r'', '', text, flags=re.DOTALL)
    
    # 3. Odstranění šablon {{...}} (opakováno pro vnořené šablony)
    for _ in range(5): 
        text = re.sub(r'\{\{[^\{\}]*?\}\}', '', text, flags=re.DOTALL)

    # 4. Odstranění formátování obrázků a souborů [[Soubor:Název|...]]
    text = re.sub(r'\[\[(Soubor|File|Obrázek):.*?\]\]', '', text, flags=re.IGNORECASE)
    
    # 5. Odstranění externích odkazů [http://...]
    text = re.sub(r'\[http[s]?://[^\s]*?\s?([^\]]*)\]', r'\1', text)
    
    # 6. Odstranění tučného/kurzívy ('')
    text = re.sub(r'\'{2,5}', '', text)

    # 7. Zpracování Wiki odkazů [[Cíl|Popis]] -> zachováme Popis
    text = re.sub(r'\[\[[^\|]*?\|([^\|]*?)\]\]', r'\1', text) 
    # Zpracování jednoduchých odkazů [[Cíl]] -> zachováme Cíl
    text = re.sub(r'\[\[([^\]]*?)\]\]', r'\1', text) 

    # 8. Odstranění nadpisů (== Nadpis ==)
    text = re.sub(r'^=+\s*.*?\s*=+$', '', text, flags=re.MULTILINE)

    # 9. Normalizace mezer a nových řádků
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    return text

# --- 3. Analýza frekvence n-gramů ---

def spocitej_digramy(text: str) -> Dict[str, float]:
    """Spočítá a vrátí relativní frekvenci po sobě jdoucích dvojic znaků (digramů)."""
    digramy = []
    
    if len(text) < 2:
        return {}

    for i in range(len(text) - 1):
        digramy.append(text[i:i+2])
        
    frekvence = Counter(digramy)
    celkovy_pocet = len(digramy)
    
    # Přepočet na relativní frekvenci (float 0.0 až 1.0)
    relativni_frekvence = {digram: pocet / celkovy_pocet 
                            for digram, pocet in frekvence.items()}
    
    return relativni_frekvence

# --- 4. Hlavní procesní funkce ---

def process_and_analyze_dump(dump_path: str):
    """
    Hlavní funkce, která zpracovává dump, čistí text a vrací finální korpus.
    """
    corpus_text = [] 
    clanok_count = 0
    
    # Množina povolených znaků pro češtinu (+ mezery a základní interpunkce)
    povolené_znaky = set("aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvyýzž.,!?():- /") 
    
    for wiki_text in get_wiki_text_from_dump(dump_path):
        
        clanok_count += 1
        
        # Tisknutí stavu každých 5000 článků pro sledování pokroku
        if clanok_count % 5000 == 0:
            print(f"   [INFO] Zpracováno článků: {clanok_count:6,}. Délka korpusu: {sum(len(t) for t in corpus_text):,} znaků.")
        
        # 1. Čištění značek
        clean_text = clean_wiki_markup(wiki_text)
        
        # 2. Standardizace na malá písmena
        final_text = clean_text.lower()
        
        # 3. Filtrace - ponechání pouze povolených znaků
        final_text = "".join(char for char in final_text if char in povolené_znaky or char == ' ')

        corpus_text.append(final_text)

    print(f"   [INFO] Hotovo! Celkový počet zpracovaných článků: {clanok_count:,}.")

    # Spojení do jednoho velkého korpusu
    final_corpus = " ".join(corpus_text)
    
    return final_corpus

# --- 5. EXECUTION ---

if __name__ == "__main__":
    # !!! UPRAVTE CESTU K VAŠEMU ROZBALENÉMU XML SOUBORU !!!
    DUMP_CEST = "cswiki-latest-pages-articles.xml"  
    
    if not os.path.exists(DUMP_CEST):
        print("🛑 CHYBA: Soubor dumpu nebyl nalezen na zadané cestě:")
        print(f"Cesta: {DUMP_CEST}")
        print("Ujistěte se, že je soubor ROZBALENÝ (ne .bz2) a cesta je správná.")
        exit()

    print(f"✅ Spouštím sběr dat z dumpu: {DUMP_CEST}")

    # A. Zpracování a čištění textu
    cisty_korpus = process_and_analyze_dump(DUMP_CEST)

    if cisty_korpus:
        # B. Výpočet frekvencí digramů
        print("\n🔬 Spouštím analýzu frekvence digramů...")
        frekvence_digramu = spocitej_digramy(cisty_korpus)

        # C. Uložení frekvencí do JSON
        try:
            # Ukládá jen digramy s frekvencí nad 0.00001 (0.001%) pro zmenšení souboru
            relevantni_digramy = {k: v for k, v in frekvence_digramu.items() if v > 0.00001} 
            
            with open("frekvence_digramu_cs.json", "w", encoding="utf-8") as f:
                json.dump(relevantni_digramy, f, ensure_ascii=False, indent=4)
                
            print(f"🎉 ÚSPĚCH: Frekvence digramů uložena do 'frekvence_digramu_cs.json'.")
            print(f"Počet relevantních digramů: {len(relevantni_digramy)}.")
            
        except Exception as e:
            print(f"🛑 CHYBA PŘI UKLÁDÁNÍ JSON: {e}")