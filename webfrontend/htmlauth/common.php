<?php
declare(strict_types=1);
require_once 'loxberry_system.php';

function eva_config(): array {
    global $lbpconfigdir;
    $path = "$lbpconfigdir/settings.json";
    if (!is_file($path)) $path = "$lbpconfigdir/defaults.json";
    $value = json_decode((string)file_get_contents($path), true, 16, JSON_THROW_ON_ERROR);
    return ['host' => (string)($value['host'] ?? ''), 'preview' => ($value['preview'] ?? true) !== false];
}

function eva_session(): void {
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_name('evastream');
        session_start(['cookie_httponly' => true, 'cookie_samesite' => 'Strict',
            'cookie_secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
            'use_strict_mode' => true]);
    }
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
}

function eva_json(array $value, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($value, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    exit;
}
