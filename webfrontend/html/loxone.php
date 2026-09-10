<?php
declare(strict_types=1);
require_once 'loxberry_system.php';
require_once "$lbpbindir/http.php";

// Deliberately outside htmlauth: Loxone authenticates with a dedicated token.
// Only the documented command allowlist is exposed, never arbitrary URLs.
try {
    if ($_SERVER['REQUEST_METHOD'] !== 'GET') eva_json(['ok'=>false,'error'=>'Gebruik GET.'], 405);
    $settings = eva_config();
    if (empty($settings['loxone_enabled'])) eva_json(['ok'=>false,'error'=>'Loxone-koppeling is uitgeschakeld.'], 403);
    $token = $_GET['token'] ?? '';
    if (!is_string($token) || strlen($settings['loxone_token']) !== 64 || !hash_equals($settings['loxone_token'], $token)) {
        eva_json(['ok'=>false,'error'=>'Ongeldige toegangssleutel.'], 401);
    }
    $payload = eva_loxone_payload($_GET);
} catch (Throwable $error) {
    eva_json(['ok'=>false,'error'=>$error->getMessage()], 400);
}
try {
    $lock = eva_lock();
    $result = eva_bridge(json_encode($payload, JSON_THROW_ON_ERROR));
    if ($payload['command'] === 'status') {
        if (empty($result['ok']) || !is_array($result['data'] ?? null)) throw new RuntimeException('Status niet beschikbaar.');
        eva_text(eva_status_values($result['data'], $settings['preview'] !== false));
    }
    eva_json($result, !empty($result['ok']) ? 200 : 502);
} catch (Throwable $error) {
    // Keep stale values out of the response; Loxone can gate them on online.
    if ($payload['command'] === 'status') eva_text(['online'=>0]);
    eva_json(['ok'=>false,'error'=>$error->getMessage()], 503);
}
