#!/bin/bash
# Run via ghvmctl exec, which supplies the desktop user's session environment.
set -euo pipefail

for attempt in {1..60}; do
    pid=$(pgrep -x SpectrumAnalyse || true) # Linux comm is limited to 15 chars.
    if [ -n "$pid" ]; then
        window=$(xdotool search --onlyvisible --pid "$pid" 2>/dev/null | head -n 1 || true)
        if [ -n "$window" ]; then
            xdotool windowactivate --sync "$window"
            sleep 10
            kill -0 "$pid"
            xdotool search --onlyvisible --pid "$pid" | grep -Fx "$window"
            xdotool getwindowname "$window"
            exit 0
        fi
    fi
    sleep 1
done
echo 'Spectrum Analyser did not keep a visible window open' >&2
exit 1
