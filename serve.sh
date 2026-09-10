#!/bin/sh
# Serve the whole site locally so absolute links (/events/, /actions/) work.
# No dependencies: uses the Python that ships with macOS.
#
#   ./serve.sh            # http://localhost:8931/  (Ctrl-C to stop)
#   PORT=9000 ./serve.sh
cd "$(dirname "$0")"
PORT="${PORT:-8931}"
echo "El Niño Ready at http://localhost:$PORT/  (Ctrl-C to stop)"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
