# EVAstream koppelen met Loxone via HTTP

Vanaf pluginversie 0.2.0. De Miniserver stuurt virtuele HTTP-uitgangen naar
LoxBerry en leest de controllerstatus via een virtuele HTTP-ingang.
Geen MQTT, Miniserver-wachtwoord of internetverbinding nodig voor de bediening.

## 1. Plugin instellen

Installeer de update zonder de plugin te verwijderen. Open EVAstream,
vink **Loxone HTTP-koppeling inschakelen** aan en sla op. Een eigen
toegangssleutel wordt aangemaakt. De pagina toont daarna kopieerbare adressen
met de juiste pluginmap en sleutel. Bestaande instellingen blijven behouden.

Laat voorbeeldmodus aan tijdens configuratie. Uitlezen werkt dan al; bediening
toont alleen de geplande opdrachten. Schakel voorbeeldmodus uit en sla op
wanneer Loxone de hardware mag bedienen. Installatie en pagina openen starten
zelf geen jet of programma.

Gebruik het **LoxBerry-adres**, niet het EVA Controller-adres. De Miniserver
moet dit adres kunnen bereiken. Als je de plugin via een externe proxy of
andere hostnaam opent, vervang die in de getoonde adressen door het lokale
LoxBerry-adres. De toegangssleutel geeft bedieningsrechten; deel de URL's niet
publiek. Uitschakelen van de koppeling maakt alle Loxone-opdrachten ontoegankelijk.

## 2. Virtuele HTTP-ingang: status

Maak in Loxone Config onder virtuele ingangen een **Virtuele HTTP-ingang**.
Kopieer de volledige status-URL uit de plugin. Gebruik:

- Opvraagcyclus: **10 seconden**.
- Timeout: **15.000 ms** (controllerverzoeken hebben maximaal 10 seconden).
- Een passende verbindingsbewaking voor een onbereikbare LoxBerry.

Voorbeeld-URL (vervang de hoofdletters door je eigen waarden):

```text
http://LOXBERRY_IP/plugins/evastream/loxone.php?token=SLEUTEL&command=status
```

Voeg daaronder virtuele HTTP-ingangscommando's toe met deze commandherkenning:

| Naam | Commandherkenning | Betekenis |
|---|---|---|
| Status beschikbaar | `online=\v` | 1 = status succesvol uitgelezen, 0 = nu niet beschikbaar |
| Voorbeeldmodus | `preview=\v` | 1 = bediening wordt alleen getoond |
| Stand-by | `standby=\v` | 1 = globale stand-by aan |
| Jet draait | `jet_running=\v` | 1 = controller meldt running en stand-by staat uit |
| Jet gepauzeerd | `jet_paused=\v` | 1 = stream.state is paused |
| Jetstatus | `jet_state=\v` | 0 idle, 1 running, 2 paused, 3 stopped, -1 onbekend |
| Intensiteit | `speed_percent=\v` | Instelling/speed gain in %, geen gemeten watersnelheid |
| Resterende tijd | `remaining_seconds=\v` | Resterende tijd voor standalone zwemmen, niet de programmatijd |
| Gebruiker | `program_user=\v` | Ruwe cur_program_user-waarde |
| Programmaslot | `program_slot=\v` | Ruwe cur_program_slot-waarde |
| Programmacue | `program_cue=\v` | Ruwe cur_program_cue-waarde |
| Streamcue | `stream_cue=\v` | Ruwe stream.cue; standalone gebruikt -2 |
| Licht zone 0 aan | `light_0_on=\v` | Afgeleid uit cue, intensiteit, zonestatus en stand-by |
| Lichtsterkte zone 0 | `light_0_brightness=\v` | Ingestelde intensiteit, 0–100% |
| Lichtcue zone 0 | `light_0_cue=\v` | 256 = uit, 261 = blauw, 264 = wit |

Voor overige zones vervang je `light_0_` door `light_1_`, `light_2_` of `light_3_`.
Alleen door de controller geleverde zones en velden worden gepubliceerd.
De status is softwareterugmelding, geen onafhankelijke fysieke sensor.
Programmagegevens kunnen buiten een programma oude of niet-relevante waarden
bevatten. Er wordt geen programma-ID geraden uit het gebruikersslot.

Als de controller niet reageert of een ander verzoek de plugin bezet houdt,
geeft de statusaanvraag alleen `online=0` terug. Andere waarden worden dan niet
vernieuwd. Gebruik **online** om de overige terugmeldingen in Loxone geldig te
verklaren. Wanneer LoxBerry zelf offline is, gebruik je ook Loxones timeoutbewaking.

## 3. Virtuele uitgang: bediening

Maak een **Virtuele uitgang** met adres `http://LOXBERRY_IP` (of het bereikbare
HTTPS-adres). De pluginpagina toont dit adres apart. Voeg onder die uitgang
commando's toe. Gebruik HTTP-methode **GET**, zonder body of extra headers.

Onderstaande waarden zijn het veld **Opdracht bij AAN**. Vervang `SLEUTEL`
en, indien nodig, de pluginmap. De plugin toont enkele volledig ingevulde
voorbeelden zodat je de sleutel niet handmatig hoeft over te typen.

| Functie | Opdracht bij AAN |
|---|---|
| Jet starten, 40%, 15 min | `/plugins/evastream/loxone.php?token=SLEUTEL&command=jet&speed=40&minutes=15` |
| Intensiteit aanpassen | `/plugins/evastream/loxone.php?token=SLEUTEL&command=speed&percent=<v>` |
| Pauzeren | `/plugins/evastream/loxone.php?token=SLEUTEL&command=pause` |
| Hervatten | `/plugins/evastream/loxone.php?token=SLEUTEL&command=resume` |
| Sessie stoppen | `/plugins/evastream/loxone.php?token=SLEUTEL&command=stop` |
| Stand-by aan | `/plugins/evastream/loxone.php?token=SLEUTEL&command=standby&state=on` |
| Stand-by uit | `/plugins/evastream/loxone.php?token=SLEUTEL&command=standby&state=off` |
| Blauw licht, zone 0, 50% | `/plugins/evastream/loxone.php?token=SLEUTEL&command=light&zone=0&color=blue&brightness=50` |
| Licht uit, zone 0 | `/plugins/evastream/loxone.php?token=SLEUTEL&command=light&zone=0&color=off` |
| Alleen lichtsterkte | `/plugins/evastream/loxone.php?token=SLEUTEL&command=brightness&zone=0&percent=<v>` |
| Programma starten | `/plugins/evastream/loxone.php?token=SLEUTEL&command=program&id=0&user=0&speed=40` |

Gebruik bij start/pauze/stop **digitale pulscommando's**. Laat Opdracht bij UIT
leeg als daar geen afzonderlijke actie nodig is. Zet automatische herhaling
uit: herhaald starten zou de training opnieuw kunnen voorbereiden.

Gebruik voor `<v>` **analoge uitgangen** (Gebruik als digitale uitgang uit).
Beperk jetsnelheid tot 30–100 en lichtsterkte tot 0–100. Geef gehele percentages;
waarden als `40.000` worden ook geaccepteerd. Een snelheidscommando start
de jet niet. Koppel de statusingangen aan terugmelding/weergave, zodat een
terugmelding niet onbedoeld weer een startcommando veroorzaakt.

De brightness-opdracht wijzigt alleen intensiteit. Kies eerst een kleur als de
lichtcue op uit staat. `light` wijzigt kleur en helderheid samen; zonder
brightness wordt 50% gebruikt. Beschikbare kleuren: off, red, yellow, green,
cyan, blue, purple, lightblue, white, cyan-blue-gradient, cyan-blue-split.

Haal programma's en gebruikers in de plugin op en gebruik hun ID's. Programma
0/gebruiker 0 zijn voorbeelden. Extra parameters voor programma's:
`slot` (bestaand gebruikersslot), `cue_index` (stapindex, standaard 0).
Een training kan de verlichting overnemen. Startopdrachten schakelen globale
stand-by uit. De plugin implementeert het kinderslot van de EVA-webapp niet.

## Antwoorden en fouten

### EVAstream-verlichting is grijs

De EVA-webapp blokkeert zone 0 tijdens een lopende **of gepauzeerde** training.
Stand-by heft die blokkering niet op. Vanaf 0.2.1 weigert de plugin daarom
licht- en brightness-opdrachten naar die zone zolang de training deze beheert.
Stop de sessie expliciet met `command=stop` of **Sessie stoppen** in de plugin
als je de training wilt beeindigen. Herlaad daarna de EVA-webapp. Een lichtopdracht
stopt of hervat de training niet automatisch. Andere zones blijven onafhankelijk
bedienbaar. De statuscontrole is geen atomaire vergrendeling met andere apps:
vermijd gelijktijdige trainings- en lichtopdrachten via verschillende bedieningen.

Grijze bediening alleen bewijst niet dat de controller vastgelopen is. Controleer
de bereikbaarheid en streamstatus. Zonder opdrachtenlog is de oorzaak van een
onverwachte programmastatus niet met zekerheid vast te stellen.

Status is tekst met een numerieke waarde per regel. Bedieningsopdrachten
geven JSON met `ok`, `preview` en `output`. `ok=true` in voorbeeldmodus betekent
dat het commando geldig is, niet dat hardware bediend is. HTTP 401: verkeerde
sleutel; 403: koppeling uit; 400: ongeldige HTTP-parameters; 502/503: opdracht
of verbinding mislukt. Bij fouten kan een deel van een reeks al uitgevoerd
zijn. Lees status uit voordat je opnieuw start.

De sleutel overleeft updates en wordt niet in de repository opgeslagen. De
koppeling ondersteunt alleen de hierboven beschreven opdrachten, geen
firmware-, gebruikers- of netwerkconfiguratie. Ze gebruikt dezelfde
opdrachtvergrendeling en voorbeeldmodus als de webpagina.

## Bronnen en validatie

[Loxone virtuele HTTP-ingang en commandherkenning](https://www.loxone.com/enus/kb/virtual-http-input/)
en [Loxone virtuele uitgangen](https://www.loxone.com/enen/kb/virtual-inputs-outputs/).
De koppeling wordt lokaal met nagebootste controllerantwoorden getest.
De daadwerkelijke configuratie/import in Loxone Config en hardwarebediening
zijn nog niet getest op een Miniserver.
