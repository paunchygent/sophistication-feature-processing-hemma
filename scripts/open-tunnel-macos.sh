#!/bin/bash
set -euo pipefail

ssh_target=${1:-paunchygent@hemma.tail730aa2.ts.net}

open http://127.0.0.1:13000/
exec ssh -N \
  -L 13000:127.0.0.1:13000 \
  -L 13001:127.0.0.1:13001 \
  "$ssh_target"
