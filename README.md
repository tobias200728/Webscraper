# CarFinder Austria 🚗

Aggregierter Gebrauchtwagen-Sucher für Österreich — **ohne Datenbank, ohne Login, ohne Speicherung**.  
Ergebnisse werden live von den Portalen geladen und direkt angezeigt.

**Durchsuchte Portale:**
- willhaben.at
- autoscout24.at
- gebrauchtwagen.at
- mobile.de (AT-Inserate)
- autoinserat.at

---

## Voraussetzungen

- **Python 3.11+** → https://www.python.org/downloads/
- **Node.js 20+** → https://nodejs.org/

Beides installieren, dann weiter.

---

## Backend starten

```powershell
cd D:\GitHub\Webscraper\backend

# Virtuelle Umgebung erstellen
python -m venv venv
.\venv\Scripts\Activate.ps1

# Pakete installieren
pip install -r requirements.txt

# Konfiguration anlegen
Copy-Item .env.example .env

# Backend starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API-Docs: http://localhost:8000/docs

---

## Frontend starten (neues Terminal)

```powershell
cd D:\GitHub\Webscraper\frontend

npm install
npm run dev
```

Anwendung: http://localhost:3000

---

## Benutzung

1. Marke und Modell eingeben (z.B. `Volkswagen` / `Golf`)
2. Optional: Preis, Kilometerstand, Farbe filtern
3. „Jetzt suchen" klicken
4. Ergebnisse erscheinen live — ein Klick auf „Inserat öffnen" öffnet das Original

---

## Neuen Scraper hinzufügen

1. Neue Datei in `backend/app/scrapers/` anlegen
2. Von `BaseScraper` erben, `name` setzen und `search()` implementieren
3. In `backend/app/scrapers/__init__.py` zu `ALL_SCRAPERS` hinzufügen

```python
class MeinPortalScraper(BaseScraper):
    name = "mein_portal"

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        # ... HTTP-Request, HTML-Parsing
        yield VehicleResult(id=..., source=self.name, title=..., listing_url=...)
```
