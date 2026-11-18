#!/usr/bin/env bash
# Installatie voor Linux Mint (en andere Ubuntu/Debian-systemen; werkt ook op Fedora).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
APP_DIR="$PWD"

echo "==> Systeempakketten installeren (sudo-wachtwoord nodig)"
if command -v apt-get >/dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-tk ffmpeg
elif command -v dnf >/dev/null; then
    sudo dnf install -y python3 python3-tkinter ffmpeg-free || sudo dnf install -y python3 python3-tkinter ffmpeg
else
    echo "Onbekende pakketbeheerder: installeer python3, venv, tkinter en ffmpeg zelf."
fi

echo "==> Python-omgeving maken"
python3 -m venv --clear .venv
.venv/bin/python -m pip install --upgrade pip
echo "==> PyTorch (CPU) installeren, ongeveer 200 MB"
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install numpy einops julius pyyaml tqdm openunmix
.venv/bin/pip install --no-deps demucs

echo "==> Startmenu-snelkoppeling maken"
chmod +x run.sh
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/vocal-remover.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Vocal Remover
Comment=Verwijder de zang uit een nummer en behoud de muziek
Exec="$APP_DIR/run.sh"
Icon=audio-x-generic
Terminal=false
Categories=AudioVideo;Audio;
EOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo
echo "Klaar! Start 'Vocal Remover' via het menu, of voer ./run.sh uit."
echo "Bij de eerste keer wordt het AI-model (80 MB) eenmalig gedownload."
