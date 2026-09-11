# Wijzigingen

## 0.2.3

- Gebruik lokale IPv4-adressen van eth0/eth1 voor de Loxone-URL's, in plaats
  van het browseradres dat via VPN kan lopen.
- Bied een aansluitingkeuze als beide interfaces een adres hebben.
- Meld ontbrekende LAN-adressen zonder terug te vallen op het VPN-adres.

## 0.2.2

- Voeg session_state, session_active, session_paused en session_locked toe aan
  de bestaande Loxone-statuspagina.
- Meld de trainingsblokkering ook bij pauze en stand-by; standalone zwemmen
  blokkeert de verlichting niet. Onbekende toestand wordt -1, niet vrij.
- Documenteer commandherkenning en Loxone-logica voor een blokkademelding.

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
