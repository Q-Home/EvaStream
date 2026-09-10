# EVA lokaal bedienen

Gebruik `eva.py` met Python 3.8 of nieuwer op dezelfde LAN als de controller.
Geen extra pakketten nodig. Standaardhost: evacontroller.local. Gebruik --host CONTROLLER_IP voor een IP-adres.
Dit is een onofficiele client, gebaseerd op de JavaScript-code van jouw controller.
GET-verzoeken zijn live gecontroleerd. Bedieningsopdrachten zijn alleen als
voorbeeld uitgevoerd: fysieke werking is nog niet getest.

## Uitlezen

```bash
python3 bin/eva.py status
python3 bin/eva.py zones
python3 bin/eva.py programs
python3 bin/eva.py users
python3 bin/eva.py colors
```

## Bedienen

Zonder `--execute` toont het script alleen de geplande POST-opdrachten.
De voorbeelden hieronder voeren de bediening echt uit.

```bash
# Blauwe verlichting op 50%, eerste zone (EVAstream)
python3 bin/eva.py --execute light blue --zone 0 --brightness 50

# Verlichting uit
python3 bin/eva.py --execute light off --zone 0

# Jet starten op 40% gedurende 15 minuten
python3 bin/eva.py --execute jet --speed 40 --minutes 15

# Intensiteit van de huidige zwemsessie aanpassen
python3 bin/eva.py --execute speed 50

# Programma 0 starten voor gebruiker 0, met expliciete intensiteit
python3 bin/eva.py --execute program 0 --user 0 --speed 50

# Eigen programma 4 starten
python3 bin/eva.py --execute program 4 --user 0 --speed 50

python3 bin/eva.py --execute pause
python3 bin/eva.py --execute resume
python3 bin/eva.py --execute stop
python3 bin/eva.py --execute standby on
```

Voor een ander IP-adres: `python3 bin/eva.py --host CONTROLLER_IP status`.
Globale opties (`--host`, `--execute`) komen voor de opdracht.

## Gedrag en grenzen

- Jet en programma starten halen de controller uit stand-by en hervatten de
  voorbereide sessie. Dit kan de zwemstroming meteen activeren.
- Lichtopdrachten wijzigen globale stand-by niet. Indien nodig zet je die
  expliciet uit: `python3 bin/eva.py --execute standby off`. Dit is een globale
  controllerfunctie, geen afzonderlijke lichtschakelaar.
- `speed` is de procentuele intensiteit/speed gain (30..100), geen meting in m/s.
  Bij programma's schaalt deze de geprogrammeerde intensiteit.
- Programma's worden live opgezocht. Bij een passend gebruikersslot wordt de
  opgeslagen snelheid gebruikt als je `--speed` weglaat. Zonder passend slot
  is `--speed` verplicht; het script volgt dan de tijdelijke slot-0-aanpak van
  de webapp. Het wijzigt geen opgeslagen programma's of gebruikersinstellingen.
- `--cue-index` kiest een stapindex binnen het programma, standaard 0;
  dit is niet het cue-ID.
- Lichtzones zijn genummerd vanaf 0. Kleuren volgen de vaste presets van de
  webapp, geen vrije RGB-waarden. Licht uit gebruikt cue 256.
- Een trainingsprogramma kan de gekoppelde verlichting overnemen.
- Er zijn geen automatische herhalingen van POST-verzoeken. Na een fout
  kan een reeks gedeeltelijk uitgevoerd zijn; lees eerst `status` uit.
- De webapp heeft een eigen kinderslot; deze client implementeert dat niet.
  De client vervangt de fysieke bediening of noodstop niet.

## Programma-ID's

Gebruik `programs` en `users` om de actuele ID's van jouw installatie op te vragen.
De ID's in de voorbeelden zijn illustratief; lege programma's worden geweigerd.
