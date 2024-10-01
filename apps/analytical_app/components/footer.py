# components/footer.py
from dash import html

def create_footer():
    footer = html.Footer(
        '© 2024 МозаикаМед',
        style={
            'position': 'fixed',
            'left': 0,
            'bottom': 0,
            'width': '100%',
            'background-color': '#f1f1f1',
            'text-align': 'center',
            'padding': '10px 0',
            'margin-left': '0',
            'z-index': '999',
        }
    )
    return footer
