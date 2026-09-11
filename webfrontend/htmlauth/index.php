<?php
require_once __DIR__ . '/common.php';
require_once 'loxberry_web.php';
require_once "$lbpbindir/network.php";
$evaLanAddresses = eva_detect_lan();
$evaLocalScheme = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' ? 'https' : 'http';
$evaLocalPort = (int)($_SERVER['SERVER_PORT'] ?? 80);
$evaPortSuffix = ($evaLocalPort > 0 && $evaLocalPort < 65536 && $evaLocalPort !== ($evaLocalScheme === 'https' ? 443 : 80)) ? ':' . $evaLocalPort : '';
eva_session();
$evaSettings = eva_config();
$evaToken = $_SESSION['csrf'];
session_write_close();
LBWeb::lbheader('EVAstream', 'https://github.com/Q-Home/EvaStream', 'help.html', true);
function h($v) { return htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8'); }
?>
<link rel="stylesheet" href="style.css">
<main id="eva" data-token="<?=h($evaToken)?>" data-loxone-path="<?=h('/plugins/' . basename($lbpconfigdir) . '/loxone.php')?>" data-loxone-key="<?=h($evaSettings['loxone_token'])?>" data-loxone-enabled="<?=$evaSettings['loxone_enabled']?'1':'0'?>">
  <p class="eyebrow">Q-HOME · LOKALE BEDIENING</p>
  <h1>Je zwembad, onder controle.</h1>
  <p id="mode">Voorbeeldmodus: opdrachten worden getoond, niet verstuurd.</p>
  <section class="panel">
    <h2>Verbinding</h2>
    <form id="settings">
      <label>Controlleradres<input id="host" placeholder="IPv4-adres van je controller" value="<?=h($evaSettings['host'])?>" required></label>
      <label class="check"><input id="preview" type="checkbox" <?=$evaSettings['preview']?'checked':''?>> Voorbeeldmodus</label>
      <label class="check"><input id="loxone-enabled" type="checkbox" <?=$evaSettings['loxone_enabled']?'checked':''?>> Loxone HTTP-koppeling inschakelen</label>
      <button>Instellingen opslaan</button>
      <button type="button" id="refresh">Status en programma’s ophalen</button>
    </form>
    <p id="status" role="status">Sla het controlleradres op en haal de status op.</p>
  </section>
  <section class="panel">
    <h2>Loxone: virtuele in- en uitgangen</h2>
    <label>Lokaal LoxBerry-adres voor Loxone<select id="loxone-lan">
      <?php if (!$evaLanAddresses): ?><option value="">Geen IPv4-adres gevonden op eth0 of eth1</option><?php endif; ?>
      <?php foreach ($evaLanAddresses as $lan): ?>
      <option data-interface="<?=h($lan['interface'])?>" value="<?=h($evaLocalScheme . '://' . $lan['address'] . $evaPortSuffix)?>"><?=h($lan['interface'] . ' · ' . $lan['address'])?></option>
      <?php endforeach; ?>
    </select></label>
    <p>Automatisch gevonden op de LoxBerry. Bij twee aansluitingen kies je het netwerk dat de Miniserver kan bereiken. Je keuze wordt in deze browser onthouden.</p>
    <p id="loxone-message">Schakel de koppeling hierboven in en sla op om de adressen te tonen.</p>
    <div id="loxone-links" hidden>
      <label>URL voor virtuele HTTP-ingang<textarea id="loxone-status-url" readonly rows="3"></textarea></label>
      <p>Stel de opvraagcyclus in op 10 seconden en de timeout op 15.000 ms.</p>
      <label>Adres voor virtuele uitgang<input id="loxone-output-host" readonly></label>
      <label>Opdracht bij AAN: jet starten (40%, 15 minuten)<textarea id="loxone-jet-url" readonly rows="3"></textarea></label>
      <label>Opdracht bij AAN: jetsnelheid (analoge waarde)<textarea id="loxone-speed-url" readonly rows="3"></textarea></label>
      <label>Opdracht bij AAN: stoppen<textarea id="loxone-stop-url" readonly rows="3"></textarea></label>
      <p>HTTP-methode: GET. Laat herhaling uit voor startopdrachten. De voorbeeldmodus geldt ook voor Loxone.</p>
      <p>Commandherkenning voor status: <code>online=\v</code>, <code>standby=\v</code>, <code>jet_running=\v</code>, <code>speed_percent=\v</code>, <code>light_0_brightness=\v</code>.</p>
      <p>Sessie: <code>session_state=\v</code> (0 vrij, 1 lopend, 2 gepauzeerd, 3 gestopt), <code>session_active=\v</code>, <code>session_paused=\v</code> en <code>session_locked=\v</code> (1 = training blokkeert zone 0). Waarde -1 betekent onbekend. Gebruik de terugmelding alleen als <code>online=1</code>.</p>
      <p>De adressen bevatten je toegangssleutel: bewaar ze binnen je eigen netwerk.
      <a href="https://github.com/Q-Home/EvaStream/blob/main/LOXONE.md" target="_blank" rel="noreferrer">Volledige handleiding en alle opdrachten</a>.</p>
    </div>
  </section>
  <div class="grid">
    <section class="panel"><h2>Verlichting</h2>
      <form id="light">
        <label>Zone<select id="zone"><option value="0">0 · EVAstream</option></select></label>
        <label>Kleur<select id="color">
          <option value="blue">Blauw</option><option value="white">Wit</option><option value="red">Rood</option>
          <option value="yellow">Geel</option><option value="green">Groen</option><option value="cyan">Cyaan</option>
          <option value="purple">Paars</option><option value="lightblue">Lichtblauw</option>
          <option value="cyan-blue-gradient">Cyaan-blauw verloop</option><option value="cyan-blue-split">Cyaan-blauw verdeeld</option>
        </select></label>
        <label>Lichtsterkte (%)<input id="brightness" type="number" min="0" max="100" step="5" value="50" required></label>
        <button>Verlichting instellen</button><button type="button" id="light-off">Licht uit</button>
      </form>
    </section>
    <section class="panel"><h2>Zwemstroming</h2>
      <form id="jet">
        <label>Intensiteit (%)<input id="speed" type="number" min="30" max="100" value="40" required></label>
        <label>Duur (minuten)<input id="minutes" type="number" min="1" max="120" value="15" required></label>
        <button>Jet starten</button><button type="button" id="speed-only">Alleen intensiteit aanpassen</button>
      </form>
      <div class="buttons"><button data-command="pause">Pauzeren</button><button data-command="resume">Hervatten</button><button class="stop" data-command="stop">Sessie stoppen</button></div>
    </section>
    <section class="panel"><h2>Trainingsprogramma</h2>
      <form id="program">
        <label>Gebruiker<select id="user" required><option value="">Eerst ophalen</option></select></label>
        <label>Programma<select id="program-id" required><option value="">Eerst ophalen</option></select></label>
        <label>Intensiteit (%)<input id="program-speed" type="number" min="30" max="100" value="40" required></label>
        <button>Programma starten</button>
      </form>
      <p>Start bij de eerste stap. De training kan de gekoppelde verlichting overnemen.</p>
    </section>
    <section class="panel"><h2>Stand-by</h2>
      <p>Geldt voor de hele controller. Jet en programma starten schakelen stand-by automatisch uit.</p>
      <div class="buttons"><button data-standby="on">Stand-by aan</button><button data-standby="off">Stand-by uit</button></div>
      <p>Licht instellen wijzigt stand-by niet. Deze plugin gebruikt het kinderslot van de EVA-webapp niet.</p>
    </section>
  </div>
  <section class="panel"><h2>Laatste resultaat</h2><pre id="result" aria-live="polite">Nog geen opdrachten uitgevoerd.</pre></section>
</main>
<script src="app.js" defer></script>
<?php LBWeb::lbfooter(); ?>
