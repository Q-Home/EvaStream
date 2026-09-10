<?php
declare(strict_types=1);

function eva_config(): array {
    global $lbpconfigdir;
    $path = "$lbpconfigdir/settings.json";
    if (!is_file($path)) $path = "$lbpconfigdir/defaults.json";
    $value = json_decode((string)file_get_contents($path), true, 16, JSON_THROW_ON_ERROR);
    return array_merge(['host'=>'', 'preview'=>true, 'loxone_enabled'=>false, 'loxone_token'=>''], $value);
}

function eva_bridge(string $raw): array {
    global $lbpbindir, $lbpconfigdir;
    set_time_limit(100);
    $process = proc_open(['/usr/bin/python3', "$lbpbindir/bridge.py", "$lbpconfigdir/settings.json"],
        [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']], $pipes);
    if (!is_resource($process)) throw new RuntimeException('Python kon niet gestart worden.');
    fwrite($pipes[0], $raw);
    fclose($pipes[0]);
    $stdout = stream_get_contents($pipes[1]); fclose($pipes[1]);
    $stderr = stream_get_contents($pipes[2]); fclose($pipes[2]);
    proc_close($process);
    $result = json_decode($stdout, true);
    if (!is_array($result)) throw new RuntimeException('Geen geldig antwoord van de plugin. ' . substr($stderr, 0, 500));
    return $result;
}

function eva_lock() {
    global $lbpconfigdir;
    $lock = fopen("$lbpconfigdir/command.lock", 'c');
    if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) throw new RuntimeException('Een opdracht is nog bezig.');
    return $lock;
}

function eva_json(array $value, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($value, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    exit;
}

function eva_text(array $values): void {
    header('Content-Type: text/plain; charset=utf-8');
    header('Cache-Control: no-store');
    foreach ($values as $key=>$value) echo $key . '=' . $value . "\n";
    exit;
}

function eva_status_values(array $s, bool $preview): array {
    if (!isset($s['stream']['state'], $s['speed_gain'], $s['standby'], $s['zones']) ||
        !is_bool($s['standby']) || !is_numeric($s['speed_gain']) || !is_array($s['zones'])) {
        throw new RuntimeException('Onvolledige controllerstatus.');
    }
    $state = $s['stream']['state'];
    $values = ['online'=>1, 'preview'=>(int)$preview, 'standby'=>(int)$s['standby'],
        'jet_running'=>(int)($state === 'running' && !$s['standby']),
        'jet_paused'=>(int)($state === 'paused'),
        'jet_state'=>['idle'=>0,'running'=>1,'paused'=>2,'stopped'=>3][$state] ?? -1,
        'speed_percent'=>0 + $s['speed_gain']];
    foreach (['standalone_remaining_duration'=>'remaining_seconds',
        'cur_program_user'=>'program_user', 'cur_program_slot'=>'program_slot',
        'cur_program_cue'=>'program_cue'] as $key=>$label) {
        if (isset($s[$key]) && is_numeric($s[$key])) $values[$label] = 0 + $s[$key];
    }
    if (isset($s['stream']['cue']) && is_numeric($s['stream']['cue'])) {
        $values['stream_cue'] = 0 + $s['stream']['cue'];
    }
    foreach (array_slice($s['zones'], 0, 4) as $i=>$zone) {
        if (isset($zone['intensity'], $zone['cue']) && is_numeric($zone['intensity']) && is_numeric($zone['cue'])) {
            $values["light_{$i}_brightness"] = 0 + $zone['intensity'];
            $values["light_{$i}_cue"] = 0 + $zone['cue'];
            $values["light_{$i}_on"] = (int)(!$s['standby'] && $zone['intensity'] > 0 &&
                $zone['cue'] != 256 && ($zone['status'] ?? '') === 'running');
        }
    }
    return $values;
}

function eva_loxone_payload(array $query): array {
    $command = $query['command'] ?? 'status';
    $allowed = ['status'=>[], 'light'=>['color','zone','brightness'],
        'brightness'=>['percent','zone'], 'speed'=>['percent'],
        'jet'=>['speed','minutes'], 'program'=>['id','user','speed','slot','cue_index'],
        'pause'=>[], 'resume'=>[], 'stop'=>[], 'standby'=>['state']];
    if (!is_string($command) || !array_key_exists($command, $allowed)) throw new RuntimeException('Onbekende opdracht.');
    $args = [];
    foreach ($query as $key=>$value) {
        if ($key === 'token' || $key === 'command') continue;
        if (!in_array($key, $allowed[$command], true) || !is_string($value)) throw new RuntimeException('Onbekende parameters.');
        if (in_array($key, ['color','state'], true)) $args[$key] = $value;
        else {
            // Loxone analogue values can be formatted as e.g. 40.000.
            if (!is_numeric($value) || !is_finite((float)$value) || (float)$value != floor((float)$value) || abs((float)$value) > 100000) {
                throw new RuntimeException('Gebruik een geheel getal voor ' . $key . '.');
            }
            $args[$key] = (int)$value;
        }
    }
    return ['command'=>$command, 'arguments'=>(object)$args];
}
