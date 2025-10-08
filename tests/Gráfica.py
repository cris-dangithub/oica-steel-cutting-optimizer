# Puedes copiar este código y ejecutarlo en un Jupyter Notebook o script de Python

import matplotlib.pyplot as plt

# Datos de ejemplo basados en tu plan de corte
barras = [
    # (diámetro, longitud_barra, [longitudes de cortes], repeticiones)
    ('#3', 9.0,  [[0.75]*9], 1),
    ('#3', 12.0, [[1.24]*7 + [0.75]*4], 1),
    ('#3', 12.0, [[1.24]*9 + [0.75]], 5),
    ('#3', 12.0, [[2.64]*4 + [1.24]], 4),
    ('#4', 12.0, [[1.2]*2 + [0.75]*12], 1),
    ('#4', 12.0, [[1.2]*10], 1),
    ('#4', 12.0, [[1.3]*4 + [1.2]*5 + [0.75]], 1),
    ('#4', 12.0, [[1.4]*3 + [1.3]*5 + [1.2]], 1),
    ('#4', 12.0, [[1.48]*7 + [1.4]], 1),
    ('#4', 12.0, [[2.16]*4 + [1.48]*2], 1),
    ('#4', 12.0, [[2.16]*5 + [0.75]], 1),
    ('#4', 12.0, [[4.49]*2 + [2.17, 0.75]], 4),
    ('#4', 12.0, [[4.631, 4.49, 2.17]], 1),
    ('#4', 12.0, [[4.631, 4.631, 2.17]], 4),
]

fig, ax = plt.subplots(figsize=(12, 8))
y = 0
colors = ['#4F81BD', '#C0504D', '#9BBB59', '#8064A2', '#F79646', '#2C4D75', '#E46C0A', '#948A54']

for idx, (diam, barra_len, patrones, reps) in enumerate(barras):
    for rep in range(reps):
        x = 0
        for i, corte in enumerate(patrones[0]):
            ax.barh(y, corte, left=x, color=colors[idx % len(colors)], edgecolor='black', height=0.8)
            x += corte
        # Dibujar el desperdicio si hay
        if x < barra_len:
            ax.barh(y, barra_len - x, left=x, color='gray', alpha=0.3, edgecolor='black', height=0.8, hatch='//')
        ax.text(barra_len + 0.1, y, f'{diam} - {barra_len}m', va='center', fontsize=8)
        y += 1

ax.set_xlabel('Longitud (m)')
ax.set_ylabel('Barra')
ax.set_title('Visualización de cortes por barra')
ax.set_yticks([])
plt.tight_layout()
plt.show()