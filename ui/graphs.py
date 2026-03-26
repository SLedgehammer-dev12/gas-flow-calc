def show_graphs(container, result):
    """Hesaplama sonuçları için grafikleri sağlanan container içine çizer."""
    if not result: return
    
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except ImportError:
        # matplotlib yoksa sessizce geç veya konsola yaz, sonuçta arayüzün ana parçası değil.
        return

    data = result.get('profile_data')
    if not data or len(data.get('distance', [])) == 0:
        # Eğer profil verisi yoksa container'ı temizle
        for widget in container.winfo_children():
            widget.destroy()
        return

    # Eski grafikleri temizle
    for widget in container.winfo_children():
        widget.destroy()

    # Figür oluştur (Tkinter Frame'i ile uyumlu olması için boyutları ayarlayabiliriz)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)
    
    # Mesafe (m) -> km çevrilebilir ama m kalsın
    dist = data['distance']
    press = [p/1e5 for p in data['pressure']] # bar
    vel = data['velocity'] # m/s

    # Basınç Grafiği
    ax1.plot(dist, press, 'b-', linewidth=2)
    ax1.set_ylabel('Basınç (bar)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.set_title('Hat Boyunca Basınç Değişimi')

    # Hız Grafiği
    ax2.plot(dist, vel, 'r-', linewidth=2)
    ax2.set_xlabel('Mesafe (m)')
    ax2.set_ylabel('Hız (m/s)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.set_title('Hat Boyunca Hız Değişimi')

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Figürü bellekten temizle
    plt.close(fig)
