# Aplikace pro LARP podle Čínského systému sociálního kreditu

Aplikace byla vyvinuta pro 15. brněnské skautské středisko Kompas. Pravidla jsou stručně sepsané přímo v aplikaci.
Pokud máte zájem o podrobnosti, neváhejte mě kontaktovat na hruska.jakub@skaut.cz.

## Požadavky
- Python (3.6)
- Flask (1.1.1)
- WTForms (2.2.1)
- tinydb (3.13.0)

## Použití
1) Stáhni si repozitář na svůj disk například pomocí:
```bash
git clone git@github.com:jakub-h/china_larp.git
```
2) Aplikaci spustíš souborem `app.py` naprříklad takto:
```bash
python app.py
```
3) Zjisti lokální IP adresu počítače, na kterém aplikace běží (na [Ubuntu](https://tecadmin.net/check-ip-address-ubuntu-18-04-desktop/) nebo [univerzálně](https://www.whatismybrowser.com/detect/what-is-my-local-ip-address)).
4) Hráči se připojí mobilem do stejné lokální sítě (například stejná WiFi) jako počítač (server) a poté mohou přistupovat k aplikaci přes webový prohlížeč. Adresu serveru znáš z předešlého kroku, port je 5000. Stačí tedy zadat do prohlížeče například `10.0.0.1:5000`.
5) Každý hráč si vytvoří účet a po přihlášení může ve hře fungovat.
6) Všichni organizátoři hry si mohou vytvořit administrátorské účty, kterými mohou kontrolovat hru (nepočítají se však mezi běžné hráče). Všechny administrátorské účty mají ekvivalentní práva. Jedinou nutnou a postačující podmínkou, která rozlišuje administrátorský účet od běžného, je předpona `"admin_"` ve jméně.


## Struktura repozitáře
Hlavní soubor s aplikací je `app.py`. Soubor `citizen.py` obstarává manipulaci s uživateli a databázemi. V souboru `utils.py` jsou pomocné funkce.

Databáze (hlavní - `db.json`, denní změny - `daily_updates.json` a uživatelé, kteří již splnili úkol hackování `hackers.json`) jsou ve složce `static`.

Složka `templates` obsahuje všechny `.html` soubory.

Aplikace loguje do souboru `debug.log`.