<?php
require_once __DIR__ . '/common.php';
require_once 'loxberry_web.php';
eva_session();
$evaSettings = eva_config();
$evaToken = $_SESSION['csrf'];
session_write_close();
LBWeb::lbheader('EVAstream', 'https://github.com/Q-Home/EvaStream', 'help.html', true);
function h($v) { return htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8'); }
?>
<link rel="stylesheet" href="style.css">
<main id="eva" data-token="<?=h($evaToken)?>">
  <p class="eyebrow">Q-HOME · LOKALE BEDIENING</p>
  <h1>Je zwembad, onder controle.</h1>
  <p id="mode">Voorbeeldmodus: opdrachten worden getoond, niet verstuurd.</p>
  <section class="panel">
    <h2>Verbinding</h2>
    <form id="settings">
      <label>Controlleradres<input id="host" placeholder="IPv4-adres van je controller" value="<?=h($evaSettings['host'])?>" required></label>
      <label class="check"><input id="preview" type="checkbox" <?=$evaSettings['preview']?'checked':''?>> Voorbeeldmodus</label>
      <button>Instellingen opslaan</button>
      <button type="button" id="refresh">Status en programma’s ophalen</button>
    </form>
    <p id="status" role="status">Sla het controlleradres op en haal de status op.</p>
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
