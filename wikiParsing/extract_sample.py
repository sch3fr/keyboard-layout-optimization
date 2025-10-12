import os

def extract_first_page_sample(dump_path: str, output_file: str = "xml_sample.txt"):
    """
    Načte pouze první část XML dumpu, dokud nenajde tag </page>,
    a uloží to do malého souboru. Tím se šetří RAM.
    """
    
    if not os.path.exists(dump_path):
        print(f"🛑 CHYBA: Soubor dumpu nebyl nalezen na cestě: {dump_path}")
        return

    print(f"✅ Hledám úryvek v: {dump_path}. Nezatěžuji RAM.")
    
    # Použijeme kódování utf-8 pro správné české znaky
    with open(dump_path, 'r', encoding='utf-8') as infile:
        
        output_lines = []
        page_found = False
        
        # Načítáme soubor řádek po řádku, ne celý najednou
        for line_number, line in enumerate(infile):
            
            # Hledáme deklarace a úvodní tagy (na začátku souboru)
            if line_number < 100 or "<page>" in line or page_found:
                
                output_lines.append(line)
                
                # Zaznamenáme, že jsme narazili na první tag <page>
                if "<page>" in line:
                    page_found = True
                    
                # Jakmile najdeme koncový tag </page>, máme celý první článek
                if page_found and "</page>" in line:
                    break
            
            # Zastavíme i po 1000 řádcích, pro jistotu
            if line_number > 1000:
                print("⚠️ Upozornění: Nalezeno přes 1000 řádků, zastavuji pro ochranu RAM.")
                break
        
    # Uložení extrahovaného textu do nového souboru
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.writelines(output_lines)
            
        print(f"🎉 ÚSPĚCH: Úryvek byl uložen do souboru: {output_file}")
        print("Tento malý soubor nyní můžete otevřít a zkopírovat jeho obsah.")
        
    except Exception as e:
        print(f"🛑 CHYBA PŘI UKLÁDÁNÍ: {e}")


if __name__ == "__main__":
    # !!! ZKONTROLUJ PŘESNOU CESTU K TVÉMU ROZBALENÉMU XML SOUBORU !!!
    DUMP_CEST = "cswiki-latest-pages-articles.xml"  
    extract_first_page_sample(DUMP_CEST)