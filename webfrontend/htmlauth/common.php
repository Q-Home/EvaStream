<?php
declare(strict_types=1);
require_once 'loxberry_system.php';
require_once "$lbpbindir/http.php";

function eva_session(): void {
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_name('evastream');
        session_start(['cookie_httponly' => true, 'cookie_samesite' => 'Strict',
            'cookie_secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
            'use_strict_mode' => true]);
    }
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
