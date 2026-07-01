"""
Схематичная визуализация почки с локализацией опухоли.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle
import matplotlib.patches as mpatches


def draw_kidney(localization: str, side: str, has_cystic: bool):
    """
    Рисует схематичное изображение почки с локализацией опухоли.
    """
    fig, ax = plt.subplots(figsize=(6, 7))

    # Почка (эллипс)
    kidney = Ellipse(
        (0.5, 0.5), width=0.5, height=0.85,
        facecolor="#e8c9c1", edgecolor="#8b4a3f", linewidth=2, zorder=1
    )
    ax.add_patch(kidney)

    # Ворота почки (сбоку)
    hilum_x = 0.32 if side == "Правая" else 0.68
    hilum = Ellipse(
        (hilum_x, 0.5), width=0.08, height=0.15,
        facecolor="#c9a89e", edgecolor="#8b4a3f", linewidth=1.2, zorder=2
    )
    ax.add_patch(hilum)

    # Локализация опухоли
    tumor_color = "#c0392b" if not has_cystic else "#f39c12"

    if localization == "Полюсная":
        # Верхний полюс
        tumor = Circle(
            (0.5, 0.78), 0.09,
            facecolor=tumor_color, edgecolor="#7b1a0e",
            linewidth=1.5, alpha=0.85, zorder=3
        )
        ax.add_patch(tumor)
        ax.text(0.5, 0.95, "Опухоль в полюсе", ha="center", fontsize=11, color="#2c4a7c")
    elif localization == "Центральная":
        # В центре
        tumor = Circle(
            (0.5, 0.5), 0.11,
            facecolor=tumor_color, edgecolor="#7b1a0e",
            linewidth=1.5, alpha=0.85, zorder=3
        )
        ax.add_patch(tumor)
        ax.text(0.5, 0.95, "Центральная локализация", ha="center", fontsize=11, color="#2c4a7c")
    elif localization == "Смешанная":
        # Опухоль вовлекает и полюс, и центр
        tumor = Ellipse(
            (0.5, 0.65), width=0.22, height=0.35,
            facecolor=tumor_color, edgecolor="#7b1a0e",
            linewidth=1.5, alpha=0.85, zorder=3
        )
        ax.add_patch(tumor)
        ax.text(0.5, 0.95, "Смешанная локализация", ha="center", fontsize=11, color="#2c4a7c")

    # Подпись стороны
    ax.text(0.5, 0.05, f"Сторона: {side}", ha="center", fontsize=10, color="#555")

    # Легенда кистозного компонента
    if has_cystic:
        ax.text(0.5, 0.01, "Опухоль с кистозным компонентом", ha="center", fontsize=9, color="#c0392b")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()

    return fig
