# ui/plots_panel.py
import math
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout

import calc


comma = FuncFormatter(lambda x, pos: f'{x:g}'.replace('.', ','))


def _style():
    plt.rcParams.update({
        'font.size': 10, 'axes.grid': True, 'grid.color': '0.78',
        'grid.linewidth': 0.6, 'lines.linewidth': 1.6, 'figure.dpi': 100,
    })


class _CanvasTab(QWidget):
    def __init__(self, figsize=(7, 5), parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=figsize)
        self.canvas = FigureCanvas(self.fig)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)


class PlotsPanel(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        _style()
        self.tab_scheme = _CanvasTab((7, 5))
        self.tab_fig3 = _CanvasTab((7, 5))
        self.tab_fig4 = _CanvasTab((10, 4.5))
        self.tab_fig5 = _CanvasTab((7, 5))

        self.addTab(self.tab_scheme, 'Рис. 2 — Схема')
        self.addTab(self.tab_fig3, 'Рис. 3 — b_кр(D)')
        self.addTab(self.tab_fig4, 'Рис. 4 — n_y и t_геом')
        self.addTab(self.tab_fig5, 'Рис. 5 — P_пол(D)')

    # ---------- публичный метод ----------
    def rebuild(self, res: dict):
        cfg = res['params']
        V = res['V']
        R_main = res['R_main']
        bk_main = res['bk_main']
        D_kr_levels = res['D_kr_levels']
        D_kr_main = res['D_kr_main']

        self._draw_scheme(self.tab_scheme, cfg, V, R_main, bk_main, D_kr_main)
        self._draw_fig3(self.tab_fig3, cfg, V, D_kr_levels, D_kr_main)
        self._draw_fig4(self.tab_fig4, cfg, V, bk_main)
        self._draw_fig5(self.tab_fig5, cfg, V, R_main, D_kr_main, res)

    # ---------- рис. 2 ----------
    def _draw_scheme(self, tab, cfg, V, R_main, bk_main, D_kr_main):
        tab.fig.clear()
        ax = tab.fig.add_subplot(111)

        dh_m = cfg['dh_m']
        t_vis = cfg['t_react_visual_s']
        rz = math.sqrt(max(bk_main * bk_main - dh_m * dh_m, 0))
        y0 = 0.3 * rz
        d = calc.d_obn(V, t_vis, rz, y0, R_main)
        x_turn = -d + V * t_vis
        th = np.linspace(0, math.pi / 2, 200)

        ax.add_patch(plt.Circle((0, 0), rz, fill=False, ls='--', color='black'))
        ax.plot(0, 0, marker='*', ms=14, color='black')
        ax.plot([-1.25 * d, 1.5 * rz], [y0, y0], ':', color='0.5')
        ax.plot([-d, x_turn], [y0, y0], '-', color='black', lw=2.5)
        ax.plot(x_turn + R_main * np.sin(th), y0 + R_main - R_main * np.cos(th),
                '-', color='black', lw=2.5)
        ax.plot([x_turn + R_main] * 2, [y0 + R_main, y0 + 1.25 * R_main],
                '-', color='black', lw=2.5)
        ax.plot(-d, y0, 'o', color='black')
        ax.plot(x_turn, y0, 'o', color='black', mfc='white')
        ax.annotate(f'R = {R_main:.0f} м', (x_turn + 0.12 * R_main, y0 + 0.55 * R_main))
        ax.annotate(f'r_з = {rz:.0f} м', (0.75 * rz, -1.2 * rz))
        ax.annotate('', xy=(-d, -1.4 * rz), xytext=(0, -1.4 * rz),
                    arrowprops=dict(arrowstyle='<->'))
        ax.annotate(f'd_обн = {d:.0f} м', (-0.6 * d, -1.3 * rz))
        ax.annotate('', xy=(-d, -0.9 * rz), xytext=(x_turn, -0.9 * rz),
                    arrowprops=dict(arrowstyle='<->'))
        ax.annotate(f'V·t_р = {V * t_vis:.0f} м', (-d, -0.8 * rz))
        ax.annotate('воспламенение', (-d, y0 + 0.12 * rz))
        ax.set_xlim(-1.35 * d, max(x_turn + R_main, 1.5 * rz) + 0.1 * d)
        ax.set_ylim(-1.8 * rz, y0 + 1.3 * R_main)
        ax.set_aspect('equal')
        ax.set_xlabel('x, м')
        ax.set_ylabel('y, м')
        ax.xaxis.set_major_formatter(comma)
        ax.yaxis.set_major_formatter(comma)
        tab.fig.tight_layout()
        tab.canvas.draw()

    # ---------- рис. 3 ----------
    def _draw_fig3(self, tab, cfg, V, D_kr_levels, D_kr_main):
        tab.fig.clear()
        ax = tab.fig.add_subplot(111)

        D_list = cfg['D_list_mm']
        p = cfg['p_MPa']
        I = cfg['I_threshold_kW_m2']
        k_list = cfg['k_t_list']

        D_grid = np.linspace(min(D_list) - 30, max(D_list) + 30, 200)
        for (name, Dk), ls, mk in zip(D_kr_levels.items(), ['-', '--', ':'], ['o', 's', '^']):
            ax.plot(D_grid, [calc.b_kr(Dk, V, x, p, I_thr=I) for x in D_grid],
                    ls=ls, color='black', label=f'D_кр = {Dk:.0f} кДж/м² ({name})')
            ax.plot(D_list, [calc.b_kr(Dk, V, x, p, I_thr=I) for x in D_list],
                    ls='none', marker=mk, color='black', ms=4)
        k_max = max(k_list)
        ax.plot(D_grid, [calc.b_kr(D_kr_main, V, x, p, k_max, I_thr=I) for x in D_grid],
                '-.', color='0.45', label=f'D_кр = {D_kr_main:.0f}, k_t = {k_max}')
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(comma)
        ax.set_xlabel('D_н, мм')
        ax.set_ylabel('b_кр, м')
        ax.legend(loc='upper left', fontsize=8)
        tab.fig.tight_layout()
        tab.canvas.draw()

    # ---------- рис. 4 ----------
    def _draw_fig4(self, tab, cfg, V, bk_main):
        tab.fig.clear()
        ax1 = tab.fig.add_subplot(121)
        ax2 = tab.fig.add_subplot(122)

        V_kmh = cfg['V_kmh']
        V_to_VS = cfg['V_to_VS']
        n_structural = cfg['n_structural']
        bank_list = cfg['bank_list_deg']
        escape_cases = cfg['escape_cases']

        Vg = np.linspace(200, 330, 200)
        n_stall = (Vg / (V_kmh / V_to_VS)) ** 2
        ax1.plot(Vg, n_stall, '-', color='black', label='по сваливанию (V/V_S)²')
        ax1.axhline(n_structural, ls='--', color='black', label=f'n_э = {n_structural:g}')
        for b, ls in zip(bank_list, [':', '-.']):
            ax1.axhline(calc.n_bank(b), ls=ls, color='0.35', label=f'крен {b:g}°')
        ax1.fill_between(Vg, 1.0, np.minimum(n_stall, n_structural), color='0.85', zorder=0)
        ax1.set_xlim(200, 330)
        ax1.set_ylim(1.0, max(3.0, n_structural + 0.5))
        ax1.set_xlabel('V, км/ч')
        ax1.set_ylabel('n_y')
        ax1.legend(loc='upper left', fontsize=8)
        ax1.set_title('а)', loc='left')

        Vg2 = np.linspace(200, 400, 200)
        for (label, bank, n_fixed), ls in zip(escape_cases, [':', '-.', '--', '-']):
            n = calc.n_bank(bank) if bank is not None else n_fixed
            ax2.plot(Vg2,
                     [math.sqrt(bk_main * (2 * calc.R_turn(v / 3.6, n) + bk_main)) / (v / 3.6)
                      for v in Vg2],
                     ls=ls, color='black', label=label)
        ax2.set_xlim(200, 400)
        ax2.set_ylim(bottom=0)
        ax2.set_xlabel('V, км/ч')
        ax2.set_ylabel(f't_геом, с (r_з = {bk_main:.0f} м)')
        ax2.legend(loc='upper right', fontsize=8)
        ax2.set_title('б)', loc='left')

        tab.fig.tight_layout()
        tab.canvas.draw()

    # ---------- рис. 5 ----------
    def _draw_fig5(self, tab, cfg, V, R_main, D_kr_main, res):
        tab.fig.clear()
        ax = tab.fig.add_subplot(111)

        D_list = cfg['D_list_mm']
        p = cfg['p_MPa']
        I = cfg['I_threshold_kW_m2']
        k_list = cfg['k_t_list']
        dh = cfg['dh_m']
        theta = cfg['theta_deg']
        lam = cfg['lambda_rupture_per_km_year']
        P_ign = cfg['P_ignition']
        t_vis = cfg['t_react_visual_s']
        t_atc = cfg['t_react_atc_s']

        P_all = []
        for t_r, color, mk, src in [(t_vis, 'black', 'o', 'визуально'),
                                    (t_atc, '0.45', 's', 'УВД')]:
            for k, ls in zip(k_list, ['-', '--', '-.', ':']):
                P = [calc.P_flight(V, t_r,
                                   calc.b_kr(D_kr_main, V, x, p, k, I_thr=I),
                                   dh, R_main, theta, lam, P_ign)
                     for x in D_list]
                P_all += [x for x in P if x > 0]
                ax.plot(D_list, P, ls=ls, marker=mk, ms=4, color=color,
                        label=f'{src} (t_р = {t_r:g} с), k_t = {k}')
        ax.axhline(1e-9, color='black', lw=1)
        ax.text(min(D_list), 1.4e-9, 'ориентир 10⁻⁹', fontsize=8)
        ax.set_yscale('log')
        if P_all:
            ax.set_ylim(min(P_all + [1e-13]) / 10, max(P_all + [1e-9]) * 10)
        ax.set_xlabel('D_н, мм')
        ax.set_ylabel('P_пол')
        ax.legend(loc='lower right', fontsize=7.5)

        tab.fig.tight_layout()
        tab.canvas.draw()