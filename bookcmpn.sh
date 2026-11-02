#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bookcompanion"
BIN_DIR="$HOME/.local/bin"

if [[ ! -f "$SCRIPT_DIR/book-comp.py" ]]; then
    echo "Error: book-comp.py must be beside this installer." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required. Install it with your Linux distribution's package manager." >&2
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR"
install -m 0644 "$SCRIPT_DIR/book-comp.py" "$APP_DIR/book-comp.py"

if [[ -d "$SCRIPT_DIR/book-db" && ! -e "$APP_DIR/book-db" ]]; then
    cp -a "$SCRIPT_DIR/book-db" "$APP_DIR/book-db"
fi

if ! python3 -m venv "$APP_DIR/.venv"; then
    echo "Could not create the Python virtual environment." >&2
    echo "On Debian/Ubuntu, install the python3-venv package, then rerun this script." >&2
    exit 1
fi

"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install \
    ebooklib pypdf beautifulsoup4 ollama chromadb

cat > "$APP_DIR/book-comp" <<'LAUNCHER'
#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
cd -- "$APP_DIR"
exec "$APP_DIR/.venv/bin/python" "$APP_DIR/book-comp.py" "$@"
LAUNCHER
chmod 0755 "$APP_DIR/book-comp"

if [[ -e "$BIN_DIR/book-comp" || -L "$BIN_DIR/book-comp" ]]; then
    existing="$(readlink -f -- "$BIN_DIR/book-comp" || true)"
    target="$(readlink -f -- "$APP_DIR/book-comp")"
    if [[ "$existing" != "$target" ]]; then
        echo "Error: $BIN_DIR/book-comp already exists and is not this installation." >&2
        echo "Move it or remove it, then rerun the installer." >&2
        exit 1
    fi
else
    ln -s "$APP_DIR/book-comp" "$BIN_DIR/book-comp"
fi

echo "Book Companion installed."
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Add $BIN_DIR to your PATH to use 'book-comp' from any directory."
fi
echo "Usage: book-comp /path/to/book.pdf"