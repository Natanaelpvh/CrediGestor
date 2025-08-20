# ui/styles.py

def _darken_color(hex_color: str, percentage: int) -> str:
    """Escurece uma cor hexadecimal em uma determinada porcentagem."""
    hex_color = hex_color.lstrip('#')
    # Converte para RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    # Escurece cada componente
    darker_rgb = tuple(max(0, int(c * (1 - percentage / 100.0))) for c in rgb)
    # Converte de volta para hexadecimal
    return f"#{darker_rgb[0]:02x}{darker_rgb[1]:02x}{darker_rgb[2]:02x}"

def get_button_style(button_type: str) -> str:
    """
    Retorna uma string de estilo QSS para um tipo de botão específico.
    Tipos suportados: 'novo', 'editar', 'excluir', 'imprimir', 'pagar'.
    """
    # Mapeamento de tipos de botão para suas cores base e de texto
    style_configs = {
        "novo":     {"base": "#27ae60", "text": "white"},      # Verde
        "editar":   {"base": "#2980b9", "text": "white"},      # Azul
        "excluir":  {"base": "#c0392b", "text": "white"},      # Vermelho
        "imprimir": {"base": "#7f8c8d", "text": "white"},      # Cinza (para imprimir e ver)
        "pagar":    {"base": "#2ecc71", "text": "white"},      # Verde Claro
    }

    config = style_configs.get(button_type)
    if not config:
        return ""  # Retorna estilo vazio se o tipo não for encontrado

    base_color = config["base"]
    text_color = config["text"]
    hover_color = _darken_color(base_color, 15)
    pressed_color = _darken_color(base_color, 30)

    return f"""
        QPushButton {{
            background-color: {base_color};
            color: {text_color};
            border: none;
            padding: 8px 12px;
            text-align: center;
            font-size: 10pt;
            font-weight: bold;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QPushButton:disabled {{
            background-color: #bdc3c7;
            color: #7f8c8d;
        }}
    """

# --- Estilos do Dashboard ---

# Estilo para os cartões de indicadores
INDICATOR_CARD_STYLE = """
    QFrame#indicatorCard {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        min-height: 100px;
    }
"""

INDICATOR_TITLE_STYLE = "font-size: 11pt; color: #636e72; font-weight: bold;"
INDICATOR_VALUE_STYLE = "font-size: 18pt; color: #2d3436; font-weight: bold;"

# Estilo para o relógio do dashboard
RELOGIO_STYLE = """
    QLCDNumber {
        background-color: #2b2b2b;
        color: #39FF14;
        border: 1px solid #444;
        border-radius: 8px;
    }
"""

# Estilo para os botões de atalho no dashboard
SHORTCUT_BUTTON_STYLE = """
    QPushButton {
        background-color: #f8f9fa;
        color: #343a40;
        border: 1px solid #dee2e6;
        padding: 10px;
        font-size: 10pt;
        font-weight: bold;
        border-radius: 15px;
    }
    QPushButton:hover {
        background-color: #e9ecef;
    }
"""