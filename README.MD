# Keyboard Layout Optimization
## ~~~ English description down below ~~~
- repozitář obsahující všechny skripty a zdrojový kód dipmlomové práce
- adresář dokument obsahuje LaTeX zdroj
    - zahrnuje i Bib soubor se všemi použitými zdroji
- adresář scripts obsahuje skripty (wow)
## Jak na to
- na spuštění skriptů tak, jak jsou popsané v závěrečné práci, je třeba získat dump wikipedie, v práci je použit [tento](https://mirror.accum.se/mirror/wikimedia.org/dumps/cswiki/20250920/})
- také musíte mít na svém zařízení nainstalován Python 3.X
- existuje posloupnost spuštění skriptů
1. wiki_parser.py - extrahuje n-gramy z korpusu
2. cost_calculator.py - počítá náklad QWERTY a následně je volán při optimalizacích pro výpočet nových nákladů
3. kterýkoliv další skript
- některé analytické skripty mají hardcoded hodnoty, pokud je chcete použít na analýzu jiného souboru je potřeba změnit jeho názve v kódu
## ~~~ English here ~~~
- a repo containing all the scripts and source code of my thesis
- document folder contains the LaTeX source for the thesis
    - that includes the full bib file with all used sources
- scripts contains scripts (wow)
## How to
- to run the scripts as described in the thesis, you will need to obtain a wikipedia dump, [I used this one](https://mirror.accum.se/mirror/wikimedia.org/dumps/cswiki/20250920/})
- you also need Python 3.X installed on your machine
- there are some dependencies on the script order, as run in the thesis
1. wiki_parser.py - extracts the n-grams from the corpus
2. cost_calculator.py - calculates the cost for QWERTY and is later called for calculating the new layout costs
3. whichever script you desire now
- please note that some of the analytics scripts have hardcoded inputs, you'll need to change the name of the file you try to analyze
