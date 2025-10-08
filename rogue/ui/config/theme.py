from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gradio.themes import ThemeClass


def get_theme() -> "ThemeClass":
    # gradio import takes a while, importing here to reduce startup time.
    from gradio.themes import Color, GoogleFont, Soft

    return Soft(
        primary_hue=Color(
            c50="#ECE9FB",
            c100="#ECE9FB",
            c200="#ECE9FB",
            c300="#6B63BF",
            c400="#494199",
            c500="#A5183A",
            c600="#332E68",
            c700="#272350",
            c800="#201E44",
            c900="#1C1A3D",
            c950="#100F24",
        ),
        secondary_hue=Color(
            c50="#ECE9FB",
            c100="#ECE9FB",
            c200="#ECE9FB",
            c300="#6B63BF",
            c400="#494199",
            c500="#494199",
            c600="#332E68",
            c700="#272350",
            c800="#201E44",
            c900="#1C1A3D",
            c950="#100F24",
        ),
        neutral_hue=Color(
            c50="#ECE9FB",
            c100="#ECE9FB",
            c200="#ECE9FB",
            c300="#6B63BF",
            c400="#494199",
            c500="#494199",
            c600="#332E68",
            c700="#272350",
            c800="#201E44",
            c900="#1C1A3D",
            c950="#100F24",
        ),
        font=[
            GoogleFont("Mulish"),
            "Arial",
            "sans-serif",
        ],
    )
