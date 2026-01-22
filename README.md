### Opis aplikacji

LE CASINO to internetowe kasyno. Poza oczywistymi funkcjonalnościami takimi jak zakładanie konta i logowanie, pozwala ono na granie w 3 gry, śledzenie swoich wygranych oraz "wykopanie" dodatkowych pieniędzy poprzez proof of work.

Elementy, które można znaleźć w LE CASINO to:

- Ekran logowania wraz z rejestracją
- Profil wraz z historią wygranych
- Zakładka do wykopywania pieniędzy poprzez szukanie sufiksu do losowo generowanego wyzwania w taki sposób, żeby wygenerowany na tej podstawie hash zwracał odpowiednią ilość zer
- Rzut monetą
- Sloty - możliwość zakręcenia do 5 maszynami jednocześnie, polega na REST API
- Ruletka "na żywo", gdzie można obstawiać wraz z innymi graczami konkretny kolor. Jest to element interakcji z resztą użytkowników, ponieważ ich zakłady będą widoczne. Gra opiera się na Web Socketach.

### Opis architektury

*diagram*

Składa się z aplikacji Django.

Elementy architektury znajdują się w tej samej prywatnej sieci w VPC, co pozwala im się ze sobą komunikować. Przed "zewnątrz" są chronione przez WAF, Internet Gateway z NAT, *coś jeszcze, tyle pamiętam tu i teraz*.

Zmienne środowiskowe są zarządzane poprzez Google Cloud, a następnie przekazywane odpowiednim serwisom - w szczególności aplikacjom, gdzie potrzebne są chociażby credentiale do baz danych, ich numery portów, adresy.

Baza danych PostgreSQL skaluje się automatycznie.

### Zastosowane technologie

Aplikacja wykorzystuje framework Django wraz z wieloma doinstalowanymi modułami w celu poprawy bezpieczeństwa i rozszerzenia strony o dodatkowe funkcjonalności, takie jak REST API, Web Sockety, CORS.

Jako bazy danych został użyty PostgreSQL do trzymania trwałych informacji (profile użytkowników, historia wygranych) jak i Redis do przechowywania informacji ulotnych (rundy ruletki, w szczególności dotyczy to aplikacji polegającej na Web Socketach).

Narzędzia CI/CD *Pałeczka Michała*

Aplikacja jest hostowana w Google Cloud. W związku z tym wykorzystano wiele już gotowych rozwiązań, w szczególności w kwestiach skalowalności i zabezpieczeń. *Dalej*

Dodatkowo, do analizy logów została podpięta Grafana. *Pałeczka Michała*

### Systemy i usługi bezpieczeństwa

- Analiza logów Grafana
- WAF
- Oczywiście HTTPS
- *coś jeszcze?*

### Kto co zrobił
##### Michał
CI/CD
Grafana
*dopisz sobie*
##### Kacper
Infrakstuktura w Google Cloud
*dopisz sobie*
##### Mateusz
Praca nad wstępnym projektem aplikacji - schematy bazy danych, omówienie technologii
Wstępny boilerplate w Django - struktura aplikacji, coinflip jako proof of concept
Autentykacja
Mechanizm zdobywania "pieniędzy" poprzez liczenie hasha
Frontend
Ruletka, web sockety

##### Adam
Praca nad wstępnym projektem aplikacji - schematy bazy danych, omówienie technologii
Wstępny boilerplate w Django - struktura aplikacji, coinflip jako proof of concept
Pierwsze API REST
Logika za slotsami
CORS, unit testy
