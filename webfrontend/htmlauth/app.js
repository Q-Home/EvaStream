'use strict';
(() => {
  const el = id => document.getElementById(id);
  let preview = el('preview').checked;
  const mode = () => { el('mode').textContent = preview ? 'Voorbeeldmodus: opdrachten worden getoond, niet verstuurd.' : 'Bediening actief: opdrachten worden direct uitgevoerd.'; };
  mode();
  let loxoneEnabled = el('eva').dataset.loxoneEnabled === '1';
  let loxoneKey = el('eva').dataset.loxoneKey;
  const lanChoiceKey = 'evastream-lan-' + el('eva').dataset.loxonePath;
  try {
    const preferred = localStorage.getItem(lanChoiceKey);
    const option = [...el('loxone-lan').options].find(o => o.dataset.interface === preferred);
    if (option) el('loxone-lan').value = option.value;
  } catch (_) {}
  function loxoneLinks(enabled, key) {
    loxoneEnabled = enabled; loxoneKey = key;
    const origin = el('loxone-lan').value;
    el('loxone-links').hidden = !enabled || !key || !origin;
    el('loxone-message').textContent = !origin ? 'Geen lokaal adres gevonden op eth0 of eth1. Controleer de netwerkaansluiting van de LoxBerry en herlaad deze pagina. Er wordt geen VPN-adres ingevuld.' : (enabled && key ? 'Kopieer deze velden naar Loxone Config. Het statusadres haalt de actuele controllerstatus op.' : 'Schakel de koppeling hierboven in en sla op om de adressen te tonen.');
    if (!key || !origin) return;
    const base = el('eva').dataset.loxonePath + '?token=' + encodeURIComponent(key);
    el('loxone-status-url').value = origin + base + '&command=status';
    el('loxone-output-host').value = origin;
    el('loxone-jet-url').value = base + '&command=jet&speed=40&minutes=15';
    el('loxone-speed-url').value = base + '&command=speed&percent=<v>';
    el('loxone-stop-url').value = base + '&command=stop';
  }
  loxoneLinks(loxoneEnabled, loxoneKey);
  el('loxone-lan').addEventListener('change', () => {
    try { localStorage.setItem(lanChoiceKey, el('loxone-lan').selectedOptions[0]?.dataset.interface || ''); } catch (_) {}
    loxoneLinks(loxoneEnabled, loxoneKey);
  });
  async function request(payload) {
    const response = await fetch('api.php', {method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':el('eva').dataset.token}, body:JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error([result.error, result.output, result.hint].filter(Boolean).join('\n'));
    return result;
  }
  async function busy(fn) {
    document.querySelectorAll('#eva button').forEach(b => b.disabled = true);
    try { await fn(); } catch (error) { el('result').textContent = error.message; }
    finally { document.querySelectorAll('#eva button').forEach(b => b.disabled = false); }
  }
  async function command(name, args = {}) {
    const result = await request({command:name, arguments:args});
    el('result').textContent = result.output;
    return result;
  }
  function options(id, items) {
    const select = el(id), previous = select.value;
    select.replaceChildren(...items.map(([value, label]) => new Option(label, value)));
    if (items.some(([v]) => String(v) === previous)) select.value = previous;
  }
  const number = id => Number(el(id).value);
  function validNumber(id) { return el(id).reportValidity(); }
  function form(id, fn) { el(id).addEventListener('submit', e => { e.preventDefault(); busy(fn); }); }
  form('settings', async () => {
    const result = await request({command:'save', host:el('host').value.trim(), preview:el('preview').checked, loxone_enabled:el('loxone-enabled').checked});
    loxoneLinks(result.loxone_enabled, result.loxone_token);
    preview = el('preview').checked; mode(); el('result').textContent = result.output;
    options('user', [['','Eerst ophalen']]); options('program-id', [['','Eerst ophalen']]);
    el('status').textContent = 'Instellingen opgeslagen. Haal de actuele status op.';
  });
  el('refresh').onclick = () => busy(async () => {
    const status = (await command('status')).data;
    el('status').textContent = `Verbonden · ${status.standby ? 'Stand-by' : 'Actief'} · Jet: ${status.stream?.state ?? 'onbekend'} · Intensiteit: ${status.speed_gain}%`;
    const zones = (await request({command:'zones'})).data;
    options('zone', zones.map((z,i) => [i, `${i} · ${z.name}${z.active ? '' : ' (inactief)'}`]));
    const users = (await request({command:'users'})).data;
    options('user', users.filter(u => u.name).map(u => [u.id,u.name]));
    const programs = (await request({command:'programs'})).data;
    options('program-id', programs.filter(p => p.cues?.length).map(p => [p.id,`${p.id} · ${p.name || 'Naamloos'}`]));
  });
  form('light', () => command('light', {color:el('color').value, zone:number('zone'), brightness:number('brightness')}));
  el('light-off').onclick = () => busy(() => command('light', {color:'off', zone:number('zone')}));
  form('jet', () => command('jet', {speed:number('speed'), minutes:number('minutes')}));
  el('speed-only').onclick = () => { if(validNumber('speed')) busy(() => command('speed',{percent:number('speed')})); };
  form('program', () => command('program', {id:number('program-id'), user:number('user'), speed:number('program-speed')}));
  document.querySelectorAll('[data-command]').forEach(b => b.onclick = () => busy(() => command(b.dataset.command)));
  document.querySelectorAll('[data-standby]').forEach(b => b.onclick = () => busy(() => command('standby',{state:b.dataset.standby})));
})();
