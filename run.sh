#!/bin/bash
# Garante que o script pare em caso de erro
set -e

# Navega para o diretÃ³rio onde o script estÃ¡ localizado
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# --- CriaÃ§Ã£o do Atalho/LanÃ§ador de Aplicativo ---

# --- ConfiguraÃ§Ã£o do Atalho/LanÃ§ador ---
APP_NAME="CrediGestor"
DESKTOP_FILE_NAME="credigestor.desktop"
LAUNCHER_DIR="$HOME/.local/share/applications"
DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")

# Caminhos completos
LAUNCHER_FILE_PATH="$LAUNCHER_DIR/$DESKTOP_FILE_NAME"
DESKTOP_SHORTCUT_PATH="$DESKTOP_DIR/$DESKTOP_FILE_NAME"

# Garante que o prÃ³prio script seja executÃ¡vel
chmod +x "$SCRIPT_DIR/run.sh"

# Cria ou atualiza o arquivo .desktop principal no diretÃ³rio de aplicaÃ§Ãµes
mkdir -p "$LAUNCHER_DIR"
cat > "$LAUNCHER_FILE_PATH" << EOL
[Desktop Entry]
Version=1.0
Name=$APP_NAME
Comment=Sistema de GestÃ£o Comercial
Exec="$SCRIPT_DIR/run.sh"
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Office;Database;
EOL

# DÃ¡ permissÃ£o de execuÃ§Ã£o para o lanÃ§ador
chmod +x "$LAUNCHER_FILE_PATH

# Se o atalho nÃ£o existir na Ã¡rea de trabalho, cria uma cÃ³pia e notifica o usuÃ¡rio.
if [ ! -f "$DESKTOP_SHORTCUT_PATH" ]; then
    if [ -d "$DESKTOP_DIR" ]; then
        cp "$LAUNCHER_FILE_PATH" "$DESKTOP_SHORTCUT_PATH"
        echo "Atalho para '$APP_NAME' criado na Ãrea de Trabalho."
    fi
fi

# --- Executa a AplicaÃ§Ã£o ---
echo "Iniciando CrediGestor..."
echo "(Aguarde, verificando e instalando dependÃªncias se necessÃ¡rio...)"

# Usa python3 para executar o script principal da aplicaÃ§Ã£o
# Executa o script principal. Se lanÃ§ado pelo atalho (.desktop), nenhum terminal serÃ¡ visÃ­vel.
# Se lanÃ§ado de um terminal existente, a saÃ­da aparecerÃ¡ aqui.
python3 start.py