<?php
declare(strict_types=1);

function eva_lan_addresses(array $interfaces): array {
    $found = [];
    foreach (['eth0', 'eth1'] as $name) {
        foreach ($interfaces as $interface) {
            if (($interface['ifname'] ?? '') !== $name || !in_array('UP', $interface['flags'] ?? [], true)) continue;
            foreach ($interface['addr_info'] ?? [] as $info) {
                $address = $info['local'] ?? '';
                if (($info['family'] ?? '') !== 'inet' || ($info['scope'] ?? '') !== 'global' ||
                    !filter_var($address, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) ||
                    preg_match('/^(127\.|169\.254\.|0\.)/', $address)) continue;
                if (!in_array(['interface'=>$name, 'address'=>$address], $found, true)) {
                    $found[] = ['interface'=>$name, 'address'=>$address];
                }
            }
        }
    }
    return $found;
}

function eva_detect_lan(): array {
    // Read only interface addresses; never use browser or forwarded host headers.
    foreach (['/usr/sbin/ip', '/sbin/ip', '/usr/bin/ip', '/bin/ip'] as $binary) {
        if (!is_executable($binary)) continue;
        $process = proc_open([$binary, '-j', '-4', 'address', 'show', 'up'],
            [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']], $pipes);
        if (!is_resource($process)) continue;
        fclose($pipes[0]);
        $output = stream_get_contents($pipes[1]); fclose($pipes[1]);
        stream_get_contents($pipes[2]); fclose($pipes[2]);
        $exit = proc_close($process);
        $interfaces = json_decode($output, true);
        if ($exit === 0 && is_array($interfaces)) return eva_lan_addresses($interfaces);
    }
    return [];
}
