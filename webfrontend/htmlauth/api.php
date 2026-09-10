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
    $lock = eva_lock();
    if (($input['command'] ?? '') === 'save') {
        $host = $input['host'] ?? '';
        if (!is_string($host) || !filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) ||
            !preg_match('/^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)/', $host)) {
            throw new RuntimeException('Vul een lokaal IPv4-adres in.');
        }
        if (!isset($input['preview']) || !is_bool($input['preview'])) throw new RuntimeException('Ongeldige voorbeeldmodus.');
        $settings = eva_config();
        $settings['host'] = $host;
        $settings['preview'] = $input['preview'];
        if (isset($input['loxone_enabled'])) {
            if (!is_bool($input['loxone_enabled'])) throw new RuntimeException('Ongeldige Loxone-instelling.');
            $settings['loxone_enabled'] = $input['loxone_enabled'];
        }
        if ($settings['loxone_enabled'] && empty($settings['loxone_token'])) {
            $settings['loxone_token'] = bin2hex(random_bytes(32));
        }
        $tmp = tempnam($lbpconfigdir, 'settings-');
        try {
            if ($tmp === false || file_put_contents($tmp, json_encode($settings, JSON_THROW_ON_ERROR)) === false) {
                throw new RuntimeException('Instellingen opslaan mislukt.');
            }
            chmod($tmp, 0600);
            if (!rename($tmp, "$lbpconfigdir/settings.json")) throw new RuntimeException('Instellingen vervangen mislukt.');
        } finally { if ($tmp !== false && is_file($tmp)) unlink($tmp); }
        eva_json(['ok'=>true,'output'=>'Instellingen opgeslagen.', 'loxone_token'=>$settings['loxone_token'], 'loxone_enabled'=>$settings['loxone_enabled']]);
    }
    // Forward the original JSON: associative decoding turns {} into [], which
    // Python correctly rejects as a non-object arguments value.
    $result = eva_bridge($raw);
    eva_json($result, !empty($result['ok']) ? 200 : 502);
} catch (Throwable $error) {
    eva_json(['ok'=>false,'error'=>$error->getMessage()], 400);
}
