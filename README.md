# EVAstream voor LoxBerry 4

Lokale bediening van EVA-verlichting, zwemstroming en trainingsprogramma's.
Inclusief een zelfstandige Python-client voor Linux. Geen cloudaccount of
extra Python-pakketten nodig.

**Versie 0.1.0 — eerste testversie.** De API is afgeleid uit de webapp van een
EVA Controller. Uitlezen is op de controller gecontroleerd; schrijfopdrachten
zijn met een nagebootste controller getest. Installatie op een echte LoxBerry
4 en fysieke bediening moeten nog worden gecontroleerd. Geen officieel
EVA-product; firmware-updates kunnen het protocol wijzigen.

## Installatie

1. Download de repository als ZIP via **Code → Download ZIP**, of bouw het
   installatiepakket met `python3 tools/build.py`.
2. Open **Pluginbeheer** in LoxBerry 4 en upload het ZIP-bestand.
3. Open **EVAstream**. Vul het lokale IPv4-adres van je EVA Controller in.
4. Laat **Voorbeeldmodus** eerst ingeschakeld, sla op en klik op
   **Status en programma's ophalen**.
5. Controleer de getoonde opdrachten. Schakel voorbeeldmodus uit en sla op
   wanneer je de installatie wilt bedienen.

De plugin vereist Python 3.8+ en de standaard PHP-omgeving van LoxBerry 4.
Er is geen achtergrondservice of herstart nodig. De webpagina gebruikt de
LoxBerry-aanmelding en is alleen beschikbaar onder de beveiligde pluginpagina.

## Functies

- Lichtkleur, lichtsterkte en uit per zone.
- Jet starten met intensiteit 30–100% en duur 1–120 minuten.
- Intensiteit van de lopende sessie aanpassen.
- Programma en gebruiker selecteren; starten vanaf de eerste stap.
- Pauzeren, hervatten, stoppen en globale stand-by.
- Status, zones, gebruikers en programma's rechtstreeks ophalen.
- Instellingen blijven bewaard tijdens pluginupdates.

Er worden geen programma's, gebruikers of netwerkinstellingen op de controller
aangemaakt of gewijzigd. Een programma starten of jet starten schakelt
stand-by uit en kan direct stroming veroorzaken. Lichtopdrachten laten globale
stand-by ongemoeid. Een trainingsprogramma kan gekoppelde verlichting overnemen.
Het kinderslot van de EVA-webapp wordt door deze client niet geïmplementeerd.

Na een verbindingsfout: lees de status opnieuw uit voordat je de opdracht
herhaalt. Opdrachten worden nooit automatisch opnieuw verstuurd; een reeks
kan bij een fout gedeeltelijk uitgevoerd zijn.

## Los script

```bash
python3 bin/eva.py --host 192.168.1.18 status
python3 bin/eva.py --host 192.168.1.18 light blue --brightness 50
python3 bin/eva.py --host 192.168.1.18 --execute jet --speed 40 --minutes 15
python3 bin/eva.py --host 192.168.1.18 --execute program 0 --user 0 --speed 40
python3 bin/eva.py --host 192.168.1.18 --execute stop
```

Zonder `--execute` toont het script wijzigingen alleen als voorbeeld.
Het zelfstandige script gebruikt zijn eigen `--host` en `--execute` opties,
onafhankelijk van de instellingen in de pluginpagina. Op LoxBerry staat het
in de `bin/plugins/<werkelijke-pluginmap>/` map onder de LoxBerry-installatie.
Zie [CLI.md](CLI.md) voor alle opdrachten.

## Ontwikkelen en testen

```bash
python3 -m unittest discover -s tests -v
php -l webfrontend/htmlauth/api.php
php -l webfrontend/htmlauth/index.php
php -l webfrontend/htmlauth/common.php
python3 tools/build.py
```

Tests gebruiken een lokale nepcontroller en activeren geen hardware.
Het bouwscript maakt `dist/EvaStream-0.1.0.zip` met Unix-rechten en LF-regels,
zonder tests, caches of persoonlijke instellingen. Automatische updates zijn
voor deze eerste testversie uitgeschakeld.

Technische basis: [LoxBerry-pluginstructuur](https://wiki.loxberry.de/entwickler/grundlagen_zur_erstellung_eines_plugins),
[officieel LoxBerry 4-voorbeeld](https://github.com/mschlenstedt/LoxBerry-Plugin-SamplePlugin-V4),
[EVA-netwerkdocumentatie](https://evaoptic.com/support/evawebapp-network-connection/).

Auteur: **Q-Home** · info@q-home.be
