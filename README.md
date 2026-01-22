# LE CASINO

Projekt zaliczeniowy na przedmiot **Bezpieczeństwo Serwerów i Aplikacji Webowych** na **Politechnice Wrocławskiej**. Specjalizacja: **Cyberbezpieczeństwo**.

LE CASINO to wieloosobowe kasyno internetowe oparte na Django, oferujące gry w czasie rzeczywistym (WebSocket) oraz klasyczne gry kasynowe (REST API).

## Technologie

<div align="center">
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/django/django-plain.svg" height="30" alt="django logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" height="30" alt="python logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" height="30" alt="postgresql logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/redis/redis-original.svg" height="30" alt="redis logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" height="30" alt="docker logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/tailwindcss/tailwindcss-original.svg" height="30" alt="tailwindcss logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg" height="30" alt="html logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/css3/css3-original.svg" height="30" alt="css logo" />
   <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" height="30" alt="javascript logo" />
</div>

## Spis treści

1. [Funkcjonalności](#1-funkcjonalności)
2. [Struktura projektu](#2-struktura-projektu)
3. [Szybki start](#3-szybki-start)
   - [3.1 Uruchomienie lokalne](#31-uruchomienie-lokalne)
   - [3.2 Uruchomienie z Docker](#32-uruchomienie-z-docker)
4. [Architektura](#4-architektura)
   - [4.1 Aplikacje Django](#41-aplikacje-django)
   - [4.2 System ruletki](#42-system-ruletki)
   - [4.3 Endpointy API](#43-endpointy-api)
   - [4.4 Modele bazy danych](#44-modele-bazy-danych)
5. [CI/CD i bezpieczeństwo](#5-cicd-i-bezpieczeństwo)
6. [Autorzy](#6-autorzy)

## 1. Funkcjonalności

**Dostępne gry:**
- **Ruletka "na żywo"** - gra multiplayer oparta na WebSocketach, gdzie gracze obstawiają kolory w czasie rzeczywistym. Zakłady innych graczy są widoczne dla wszystkich.
- **Sloty** - automat do gier z siatką 3x3 emoji, możliwość uruchomienia do 5 maszyn jednocześnie (REST API)
- **Coinflip** - prosty rzut monetą

**System użytkowników:**
- Rejestracja i logowanie (zabezpieczone kodem PIN)
- Profil użytkownika z historią wygranych
- Audit log wszystkich operacji

**System ekonomii:**
- "Wykopywanie" pieniędzy poprzez proof-of-work (szukanie sufiksu generującego hash z odpowiednią liczbą zer)

## 2. Struktura projektu

```
letsgogambling/
├── .github/              # GitHub Actions (CI/CD, MegaLinter)
├── casino/               # Główny projekt Django
│   ├── api/              # Endpointy DRF (balance, spin)
│   ├── base/             # Wspólne modele (History, Codes)
│   ├── coinflip/         # Gra w rzut monetą
│   ├── login/            # Autentykacja (custom User model)
│   ├── roulette/         # Ruletka multiplayer (WebSocket)
│   ├── slots/            # Automaty do gier (REST API)
│   └── user_mgr/         # Profil, saldo, mining
├── static/               # Pliki statyczne (CSS, JS)
├── templates/            # Szablony HTML
├── docker-compose.yml    # Konfiguracja Docker
├── Dockerfile            # Obraz aplikacji
├── requirements.txt      # Zależności Python
└── README.md             # Ten plik
```

## 3. Szybki start

### 3.1 Uruchomienie lokalne

**Wymagania:** Python 3.13+, Redis (127.0.0.1:6379), PostgreSQL

```bash
# Utworzenie środowiska wirtualnego
python -m venv .venv
source .venv/bin/activate

# Instalacja zależności
pip install -r requirements.txt

# Migracje bazy danych
python manage.py migrate
python manage.py createsuperuser

# Uruchomienie serwera (wymaga Redis)
daphne -b 0.0.0.0 -p 8000 casino.asgi:application

# W osobnym terminalu - uruchomienie pętli gry ruletki
python manage.py run_roulette_game
```

### 3.2 Uruchomienie z Docker

```bash
# Skopiuj i skonfiguruj zmienne środowiskowe
cp .env.example .env

# Uruchom wszystkie serwisy
docker-compose up

# Aplikacja dostępna pod http://localhost:8000
```

## 4. Architektura

### 4.1 Aplikacje Django

| Aplikacja | Opis |
| :--- | :--- |
| `casino/` | Główne ustawienia projektu, konfiguracja ASGI/WSGI, routing URL |
| `casino/roulette/` | Ruletka multiplayer (WebSocket, Django Channels) |
| `casino/slots/` | Automaty do gier - siatka 3x3 emoji (REST API) |
| `casino/coinflip/` | Rzut monetą (POST) |
| `casino/login/` | Custom User model, autentykacja |
| `casino/user_mgr/` | Profil, zarządzanie saldem, mining (proof-of-work) |
| `casino/base/` | Wspólne modele (History, Codes) |
| `casino/api/` | Endpointy DRF dla salda i spinów |

### 4.2 System ruletki

Ruletka wykorzystuje architekturę background process + WebSocket:

1. Komenda `run_roulette_game` uruchamia ciągłą pętlę tworzącą rundy gry (`GameRound`)
2. Każda runda: **15s obstawianie** → **3s kręcenie** → **obliczenie wypłat**
3. `consumers.py` obsługuje połączenia WebSocket przez Django Channels
4. Redis channel layer rozgłasza stan gry do wszystkich połączonych graczy

**Koło ruletki (54 sloty):**

| Kolor | Ilość | Mnożnik |
| :--- | :---: | :---: |
| GRAY | 26 | 2x |
| RED | 17 | 3x |
| BLUE | 10 | 5x |
| GOLD | 1 | 50x |

### 4.3 Endpointy API

| Zasób | Metoda | Endpoint | Opis |
| :--- | :--- | :--- | :--- |
| **Strony** | `GET` | `/` | Ruletka (WebSocket: `ws://host/ws/roulette/`) |
| | `GET` | `/slots/` | Sloty |
| | `GET` | `/coinflip/` | Coinflip |
| | `GET` | `/profile/` | Profil użytkownika |
| | `GET` | `/add_money/` | Interfejs miningu |
| **Auth** | `GET/POST` | `/login/` | Logowanie/rejestracja |
| **API** | `GET` | `/api/balance/` | Pobranie salda użytkownika |
| | `POST` | `/api/spin/` | Wykonanie spinu na automacie |

### 4.4 Modele bazy danych

- **User** (custom AbstractBaseUser): `username`, `balance`, `is_active`, `is_staff`
- **GameRound**: `round_number`, `status` (BETTING/SPINNING/COMPLETED), `winning_color`, `winning_slot`
- **Bet**: `user`, `round`, `color`, `amount`, `payout` (unikalny per user/round/color)
- **History**: historia wszystkich wygranych dla profili użytkowników

## 5. CI/CD i bezpieczeństwo

### Pipeline CI/CD

- **MegaLinter** - automatyczna analiza kodu przy każdym push/PR
  - `PYTHON_RUFF` - linter Python
  - `PYTHON_BANDIT` - analiza bezpieczeństwa (SAST)
  - `HTML_DJLINT` - linter szablonów Django

### Zastosowane zabezpieczenia

- **HTTPS** - szyfrowana komunikacja
- **CORS** - kontrola dostępu między domenami (`django-cors-headers`)
- **Audit logging** - logowanie wszystkich operacji (`django-auditlog`)
- **Security headers** - zabezpieczone nagłówki HTTP
- **Non-root Docker** - kontener uruchamiany jako użytkownik niepriwilejowany
- **Healthcheck** - monitoring stanu aplikacji

### Bazy danych

- **PostgreSQL** - dane trwałe (użytkownicy, historia wygranych)
- **Redis** - dane ulotne (rundy ruletki, channel layer WebSocket)

## 6. Autorzy

| Autor | Zakres prac                                                                                                                                                                            |
| :--- |:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Michał** | CI/CD, Grafana, monitoring                                                                                                                                                             |
| **Kacper** | Infrastruktura Google Cloud                                                                                                                                                            |
| **Mateusz** | Projekt aplikacji, schematy bazy danych,backend Django, autentykacja, proof-of-work (dodawanie funduszy), frontend, coinflip, ruletka (WebSocket), zabezpieczenie headerów, Dockerfile |
| **Adam** | Projekt aplikacji, schematy bazy danych, boilerplate Django, coinflip (PoC), REST API, logika slotów, CORS, unit testy                                                                 |
