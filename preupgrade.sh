#!/bin/bash
set -eu
# The installer provides the actual (possibly suffixed) plugin folder.
if [ -f "${LBPCONFIG:?}/$3/settings.json" ]; then
    cp "${LBPCONFIG}/$3/settings.json" "${6:?}/evastream-settings.backup"
fi
