#!/bin/bash
set -eu
if ! python3 -c 'import sys; assert sys.version_info >= (3, 8)' ; then
    echo '<ERROR> Python 3.8 of nieuwer is vereist.'
    exit 2
fi
