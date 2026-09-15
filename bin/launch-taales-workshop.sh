#!/bin/bash
set -euo pipefail

app=/config/workspace/tools/taales_2.2/TAALES_2.2

if [[ ! -x "$app" ]]; then
  xmessage -center "TAALES 2.2 is not installed at:\n$app\n\nSee START-HERE.txt on the desktop."
  exit 1
fi

"$app" &
app_pid=$!
window_id=""

for attempt in $(seq 1 40); do
  window_id=$(xdotool search --onlyvisible --name '^TAALES Version 2.2$' 2>/dev/null | tail -1 || true)
  [[ -n "$window_id" ]] && break
  sleep 0.25
done

if [[ -n "$window_id" ]]; then
  read -r screen_width screen_height < <(xdotool getdisplaygeometry)
  width=900
  height=1300
  (( height > screen_height - 120 )) && height=$((screen_height - 120))
  x=$(((screen_width - width) / 2))
  xdotool windowsize "$window_id" "$width" "$height"
  xdotool windowmove "$window_id" "$x" 70
  xdotool windowactivate --sync "$window_id"
fi

wait "$app_pid"
