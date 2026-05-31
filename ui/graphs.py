from translations import t
from theme_colors import resolve_colors


def show_graphs(container, result, app=None):
    """Hesaplama sonuçları için grafikleri sağlanan container içine çizer."""
    if not result: return
    
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except ImportError:
        return

    data = result.get('profile_data')
    if not data or len(data.get('distance', [])) == 0:
        for widget in container.winfo_children():
            widget.destroy()
        return

    for widget in container.winfo_children():
        widget.destroy()

    theme = getattr(app, "current_theme", "light") if app else "light"
    colors = resolve_colors(theme)

    if theme == "dark":
        grid_color = "#2c2c38"
        line1_color = colors["accent"]
        line2_color = colors.get("accent2", "#b388ff")
    elif theme == "contrast":
        grid_color = "#ffffff"
        line1_color = "#ffff00"
        line2_color = "#00ffff"
    else:
        grid_color = "#e0e0e0"
        line1_color = "blue"
        line2_color = "red"

    card_color = colors["card_bg"]
    bg_color = colors["bg"]
    text_color = colors["txt_dark"]

    # Figür oluştur
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)
    
    # Arka plan renklerini ayarla
    fig.patch.set_facecolor(bg_color)
    
    # Profil verileri
    dist = data['distance']
    press = [p/1e5 for p in data['pressure']]  # bar
    vel = data['velocity']  # m/s

    # Basınç Grafiği
    ax1.set_facecolor(card_color)
    ax1.plot(dist, press, color=line1_color, linewidth=2)
    ax1.set_ylabel(t("chart_pressure"), color=line1_color)
    ax1.tick_params(axis='y', labelcolor=line1_color, colors=text_color)
    ax1.tick_params(axis='x', colors=text_color)
    ax1.grid(True, linestyle='--', alpha=0.7, color=grid_color)
    ax1.set_title(t("chart_pressure_profile"), color=text_color)
    for spine in ax1.spines.values():
        spine.set_color(grid_color)

    # Hız Grafiği
    ax2.set_facecolor(card_color)
    ax2.plot(dist, vel, color=line2_color, linewidth=2)
    ax2.set_xlabel(t("chart_distance"), color=text_color)
    ax2.set_ylabel(t("chart_velocity"), color=line2_color)
    ax2.tick_params(axis='y', labelcolor=line2_color, colors=text_color)
    ax2.tick_params(axis='x', colors=text_color)
    ax2.grid(True, linestyle='--', alpha=0.7, color=grid_color)
    ax2.set_title(t("chart_velocity_profile"), color=text_color)
    for spine in ax2.spines.values():
        spine.set_color(grid_color)

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Figürü bellekten temizle
    plt.close(fig)
