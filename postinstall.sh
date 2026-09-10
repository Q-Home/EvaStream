#!/bin/bash
set -eu
config_dir="${LBPCONFIG:?}/$3"
mkdir -p "$config_dir"
if [ -f "${6:?}/evastream-settings.backup" ]; then
    cp "$6/evastream-settings.backup" "$config_dir/settings.json"
elif [ ! -f "$config_dir/settings.json" ]; then
    cp "$config_dir/defaults.json" "$config_dir/settings.json"
fi
chmod 600 "$config_dir/settings.json"
chmod 755 "${LBPBIN:?}/$3/eva.py" "${LBPBIN}/$3/bridge.py"
echo '<OK> EVAstream geinstalleerd. Open de plugin en stel het controlleradres in.'
