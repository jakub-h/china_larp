# Aplikace pro LARP podle Čínského systému sociálního kreditu

Aplikace byla vyvinuta pro 15. brněnské skautské středisko Kompas. Pravidla jsou stručně sepsané přímo v aplikaci.
Pokud máte zájem o podrobnosti, neváhejte mě kontaktovat na hruska.jakub@skaut.cz.

## Požadavky
- Python (doporučeno **3.12**; minimum **3.11**)
- Závislosti jsou v `pyproject.toml` (Flask, WTForms, TinyDB)

## Použití
1) Stáhni si repozitář na svůj disk například pomocí:
```bash
git clone git@github.com:jakub-h/china_larp.git
```
2) Vytvoř si virtuální prostředí a nainstaluj závislosti:
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```
3) Aplikaci spustíš souborem `app.py` naprříklad takto:
```bash
python app.py
```
4) Zjisti lokální IP adresu počítače, na kterém aplikace běží (na [Ubuntu](https://tecadmin.net/check-ip-address-ubuntu-18-04-desktop/) nebo [univerzálně](https://www.whatismybrowser.com/detect/what-is-my-local-ip-address)).
5) Hráči se připojí mobilem do stejné lokální sítě (například stejná WiFi) jako počítač (server) a poté mohou přistupovat k aplikaci přes webový prohlížeč. Adresu serveru znáš z předešlého kroku, port je 5000. Stačí tedy zadat do prohlížeče například `10.0.0.1:5000`.
6) Každý hráč si vytvoří účet a po přihlášení může ve hře fungovat.
7) Všichni organizátoři hry si mohou vytvořit administrátorské účty, kterými mohou kontrolovat hru (nepočítají se však mezi běžné hráče). Všechny administrátorské účty mají ekvivalentní práva. Jedinou nutnou a postačující podmínkou, která rozlišuje administrátorský účet od běžného, je předpona `"admin_"` ve jméně.

## Docker / Devcontainer
- Devcontainer (`.devcontainer/devcontainer.json`) si image buildí sám z `docker/Dockerfile` a používá interpreter `/opt/venv/bin/python`.
- Lokální spuštění v Dockeru:
```bash
./docker/build.sh
./docker/run.sh
```

## Doporučené nasazení pro akci (Option A: vlastní Wi‑Fi + router)
- Nech aplikaci běžet na jednom zařízení v síti (mini‑PC / notebook) a na routeru nastav:
  - DHCP reservation pro server (stálá IP)
  - lokální DNS jméno (např. `china.larp`)
- Spusť aplikaci a dej hráčům jednu adresu + QR:
```bash
# pokud na routeru máš DNS "china.larp", doporučeno:
PUBLIC_BASE_URL="http://china.larp:5000/" ./docker/run.sh
```
- Na úvodní stránce se zobrazuje **Adresa hry** a QR kód.

### Je HTTP v prohlížeči OK?
- Ano: pro **lokální Wi‑Fi na akci** je HTTP běžně v pohodě (maximálně uvidíš “Not secure”, ale stránka funguje).
- Tohle není bankovní aplikace; důležitější je bezproblémové připojení pro všechny hráče.

### (Volitelně) port 80 bez `:5000`
Pokud chceš, aby hráči psali jen `http://china.larp/`, můžeš mapovat port 80 na 5000:
```bash
HOST_PORT=80 PUBLIC_BASE_URL="http://china.larp/" ./docker/run.sh
```
Pozn.: porty <1024 můžou vyžadovat spuštění Dockeru se zvýšenými právy (typicky `sudo`).


## Struktura repozitáře
Hlavní soubor s aplikací je `app.py`. Soubor `citizen.py` obstarává manipulaci s uživateli a databázemi. V souboru `utils.py` jsou pomocné funkce.

Databáze (hlavní - `db.json`, denní změny - `daily_updates.json` a uživatelé, kteří již splnili úkol hackování `hackers.json`) jsou ve složce `static`.

Složka `templates` obsahuje všechny `.html` soubory.

Aplikace loguje do souboru `debug.log`.
