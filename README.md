# System Metali - Inteligentny System Analizy Inwestycji w Metale Szlachetne

Aplikacja desktopowa do analizy inwestycji w metale szlachetne opracowana w języku Python.

## Opis projektu

System Metali umożliwia monitorowanie inwestycji w złoto i srebro poprzez rejestrowanie transakcji zakupu, analizę wartości portfela oraz obliczanie stopy zwrotu ROI na podstawie aktualnych danych rynkowych.

Aplikacja została stworzona jako projekt rozwijany w ramach studiów na kierunku Informatyka w Biznesie.

## Główne funkcjonalności

* zarządzanie portfelem inwestycyjnym,
* dodawanie i usuwanie transakcji,
* pobieranie aktualnych kursów metali szlachetnych,
* analiza zysków i strat,
* obliczanie ROI,
* wizualizacja danych za pomocą wykresów,
* przechowywanie danych w bazie SQLite,
* historia notowań metali,
* tryb jasny i ciemny,
* moduł edukacyjny.

## Technologie

* Python
* CustomTkinter
* SQLite
* Matplotlib
* Requests
* PyInstaller
* GoldAPI
* TradingView

## Architektura

Aplikacja wykorzystuje architekturę klienta desktopowego zintegrowanego z zewnętrznymi źródłami danych rynkowych. Dane użytkownika przechowywane są lokalnie w bazie SQLite, natomiast aktualne notowania pobierane są z serwisów GoldAPI, TradingView oraz Narodowego Banku Polskiego.

## Konfiguracja API

Aplikacja wykorzystuje zewnętrzne źródło danych GoldAPI do pobierania aktualnych notowań metali szlachetnych.

Ze względów bezpieczeństwa klucz API nie jest przechowywany w repozytorium GitHub.

W celu skonfigurowania dostępu do API należy utworzyć plik:

```text
KluczApi.json
```

na podstawie pliku:

```text
KluczApi.example.json
```

i uzupełnić go własnym kluczem:

```json
{
    "gold_api_key": "TWÓJ_KLUCZ_API"
}
```

Po zapisaniu pliku aplikacja automatycznie odczyta klucz podczas uruchamiania.

## Rozwój projektu

### Wersja 2.0

* dashboard inwestycyjny,
* analiza ROI,
* wykresy,
* tryb ciemny,
* obsługa portfela.

### Wersja 3.0

* modernizacja interfejsu użytkownika,
* wykorzystanie biblioteki CustomTkinter,
* wdrożenie bazy danych SQLite,
* historia notowań metali,
* poprawa ergonomii aplikacji,
* ulepszenie wyglądu dashboardu.

## Autor

Oskar Kruszczyński – 60582

Kierunek: Informatyka w Biznesie
