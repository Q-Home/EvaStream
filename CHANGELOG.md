# Wijzigingen

## 0.2.1

- Weiger licht- en brightness-opdrachten naar zone 0 wanneer een training
  loopt of gepauzeerd is, net als de EVA-webapp. Dit geldt ook in stand-by.
- Controleer de actuele streamstatus voor deze gedeelde verlichtingszone.
- Laat overige zones en standalone zwemmen ongemoeid.
- Stop of hervat nooit automatisch een training om een lichtopdracht uit te voeren.

## 0.2.0

- Loxone virtuele HTTP-uitgangen voor jet, programma's, licht en stand-by.
- Numerieke statuspagina voor virtuele HTTP-ingangen, inclusief beschikbaarheid.
- Optionele toegangssleutel en kopieerbare adressen in de pluginpagina.
- Aparte brightness-opdracht die de lichtkleur ongemoeid laat.
- Gezamenlijke opdrachtvergrendeling en voorbeeldmodus voor web en Loxone.

## 0.1.2

- Ondersteuning voor automatische LoxBerry-updates via GitHub.
- Updateverwijzing gebruikt een vaste commit voor elke gepubliceerde versie.
- Bevat de parametercorrectie uit 0.1.1.

## 0.1.1

- Behoud lege JSON-objecten bij het doorgeven van opdrachten van PHP naar Python.
- Herstel 'Onbekende parameters' bij onder andere status, pauze en stop.
- Voeg vier regressietests voor de PHP/Python-overdracht toe.

## 0.1.0

- Eerste testversie met verlichting, jet, programma's en lokale Python-client.
