#!/bin/bash
set -e

xsetroot -solid '#e9ecef'
openbox-session &
/opt/workshop/bin/workshop-launch suite &
wait
