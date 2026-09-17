#!/bin/bash
set -euo pipefail

# One supervised SSH connection owns every persistent Mac-to-Hemma forward.
# Interactive SSH and Codex sessions are separate workloads, not tunnel daemons.
exec /usr/bin/ssh -N -T \
  -o BatchMode=yes \
  -o Compression=no \
  -o ConnectTimeout=10 \
  -o ExitOnForwardFailure=yes \
  -o ForwardAgent=no \
  -o ForwardX11=no \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -o StrictHostKeyChecking=yes \
  -L 127.0.0.1:13000:127.0.0.1:13000 \
  -L 127.0.0.1:13001:127.0.0.1:13001 \
  -L 127.0.0.1:18085:127.0.0.1:8085 \
  -L 127.0.0.1:19000:127.0.0.1:9000 \
  -L 127.0.0.1:19100:127.0.0.1:9010 \
  -L 127.0.0.1:28085:127.0.0.1:28085 \
  hemma
