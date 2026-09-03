#!/usr/bin/env bash
# Rebuild index.html. The four steps must run in this order.
set -e
cd "$(dirname "$0")/src"
python3 build_app.py
python3 add_sfx.py
python3 add_glow.py
python3 add_texture.py
mv pancake-app.html ../index.html
echo "→ index.html"
