import json

def analyze_ngrams(filename: str, top_n: int = 20, title: str = "Top N-gramy", ignore_spaces: bool = True):
    """
    Načte JSON s n-gramy, seřadí je podle četnosti a vypíše top N výsledků.
    Pokud je ignore_spaces True, vynechá jakýkoliv n-gram obsahující mezeru.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # filtrace mezer
        if ignore_spaces:
            # Ponechá jen ty n-gramy, ve kterých se nevyskytuje znak mezery
            data = {ngram: count for ngram, count in data.items() if ' ' not in ngram}
            
        # 1. Seřazení slovníku
        sorted_ngrams = sorted(data.items(), key=lambda item: item[1], reverse=True)
        
        # 2. Zjištění celkového počtu
        total_count = sum(data.values())
        
        print(f"\n{'='*50}")
        print(f" 🏆 {title.upper()} (TOP {top_n})")
        print(f"{'='*50}")
        
        # 3. Výpis top výsledků
        for i, (ngram, count) in enumerate(sorted_ngrams[:top_n], start=1):
            percent = (count / total_count) * 100 if total_count > 0 else 0
            display_ngram = ngram.replace(' ', '_')
            bar_length = int(percent * 2) 
            bar = '█' * bar_length
            
            print(f"{i:2}. | '{display_ngram:<3}' | {percent:5.2f}% | ({count:9,} x) | {bar}")
            
        print(f"{'='*50}")
        print(f"Celkem analyzováno: {total_count:,} výskytů.\n")

    except Exception as e:
        print(f"❌ Chyba: {e}")

if __name__ == "__main__":
    # analyzuje frekvence, počítá s výchozími názvy souborů

    analyze_ngrams("frekvence_digramu_cs.json", top_n=20, title="Nejčastější české digramy")
    analyze_ngrams("frekvence_trigramu_cs.json", top_n=20, title="Nejčastější české trigramy")
    
    # Pro testování lze odkomentovat tento dummy slovník:
    """
    test_data = {"po": 1500, "st": 1200, " a ": 2500, "ne": 900, " k ": 1800, "ov": 1100}
    with open("test_ngrams.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f)
    analyze_ngrams("test_ngrams.json", top_n=5, title="Test Digramů")
    """