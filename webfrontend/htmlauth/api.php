<?php
declare(strict_types=1);
require_once __DIR__ . '/common.php';
eva_session();
try {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') eva_json(['ok'=>false,'error'=>'Gebruik POST.'], 405);
    if (!hash_equals($_SESSION['csrf'], $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) {
        eva_json(['ok'=>false,'error'=>'Sessie verlopen. Herlaad de pagina.'], 403);
    }
    session_write_close();
    $raw = file_get_contents('php://input', false, null, 0, 8193);
    if (strlen($raw) > 8192) eva_json(['ok'=>false,'error'=>'Aanvraag te groot.'], 413);
    $input = json_decode($raw, true, 16, JSON_THROW_ON_ERROR);
    if (!is_array($input)) throw new RuntimeException('Ongeldige aanvraag.');
    // Serialize commands across browser sessions to prevent interleaved starts.
    $lock = fopen("$lbpconfigdir/command.lock", 'c');
    if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) eva_json(['ok'=>false,'error'=>'Een opdracht is nog bezig.'], 409);
    if (($input['command'] ?? '') === 'save') {
        $host = $input['host'] ?? '';
        if (!is_string($host) || !filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) ||
            !preg_match('/^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)/', $host)) {
            throw new RuntimeException('Vul een lokaal IPv4-adres in.');
        }
        if (!isset($input['preview']) || !is_bool($input['preview'])) throw new RuntimeException('Ongeldige voorbeeldmodus.');
        $tmp = tempnam($lbpconfigdir, 'settings-');
        try {
            if ($tmp === false || file_put_contents($tmp, json_encode(['host'=>$host,'preview'=>$input['preview']], JSON_THROW_ON_ERROR)) === false) {
                throw new RuntimeException('Instellingen opslaan mislukt.');
            }
            chmod($tmp, 0600);
            if (!rename($tmp, "$lbpconfigdir/settings.json")) throw new RuntimeException('Instellingen vervangen mislukt.');
        } finally { if ($tmp !== false && is_file($tmp)) unlink($tmp); }
        eva_json(['ok'=>true,'output'=>'Instellingen opgeslagen.']);
    }
    // Array form invokes Python directly, without shell interpolation.
    $process = proc_open(['/usr/bin/python3', "$lbpbindir/bridge.py", "$lbpconfigdir/settings.json"],
        [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']], $pipes);
    if (!is_resource($process)) throw new RuntimeException('Python kon niet gestart worden.');
    // Forward the original JSON: associative decoding turns {} into [], which
    // Python correctly rejects as a non-object arguments value.
    fwrite($pipes[0], $raw);
    fclose($pipes[0]);
    $stdout = stream_get_contents($pipes[1]); fclose($pipes[1]);
    $stderr = stream_get_contents($pipes[2]); fclose($pipes[2]);
    proc_close($process);
    $result = json_decode($stdout, true);
    if (!is_array($result)) throw new RuntimeException('Geen geldig antwoord van de plugin. ' . substr($stderr, 0, 500));
    eva_json($result, !empty($result['ok']) ? 200 : 502);
} catch (Throwable $error) {
    eva_json(['ok'=>false,'error'=>$error->getMessage()], 400);
}
