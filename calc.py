# calc.py
import math
import numpy as np

trapz = getattr(np, 'trapezoid', None) or np.trapz


# ---------- физика ----------
def r_pir(D_mm, p):
    return 0.685 * 0.3048 * (D_mm / 25.4) * math.sqrt(p * 145.038)


def dose_pass(b, V, D_mm, p, k_t=1, I_thr=15.8):
    return math.pi * k_t * I_thr * r_pir(D_mm, p) ** 2 / (V * b)


def b_kr(D_kr, V, D_mm, p, k_t=1, I_thr=15.8):
    return math.pi * k_t * I_thr * r_pir(D_mm, p) ** 2 / (V * D_kr)


def D_kr_material(m):
    return m['rho'] * m['c'] * m['delta_mm'] * 1e-3 * m['dT_K'] / m['alpha'] / 1000


def n_bank(deg):
    return 1 / math.cos(math.radians(deg))


def n_allowed(V, V_S, bank_deg, n_structural):
    return min(n_structural, (V / V_S) ** 2, n_bank(bank_deg))


def a_lat(n):
    return 9.81 * math.sqrt(n * n - 1)


def R_turn(V, n):
    return V * V / a_lat(n)


def d_obn(V, t_r, rz, y0, R):
    return V * t_r + math.sqrt(max((rz - y0) * (2 * R + rz + y0), 0.0))


def window(V, t_r, bk, y0, dh, R):
    y0 = np.asarray(y0, dtype=float)
    b0 = np.hypot(y0, dh)
    rz = math.sqrt(max(bk * bk - dh * dh, 0.0))
    with np.errstate(all='ignore'):
        geom = np.sqrt(np.clip((rz - y0) * (2 * R + rz + y0), 0, None))
        x_min = np.where(b0 > 0, b0 * np.tan(np.pi * (b0 / bk - 0.5)), -bk / np.pi)
        T = np.where(b0 < bk, np.clip((V * t_r + geom - x_min) / V, 0, None), 0.0)
    return T


def P_flight(V, t_r, bk, dh, R, theta, lam, P_ign):
    if dh >= bk:
        return 0.0
    rz = math.sqrt(bk * bk - dh * dh)
    ys = np.linspace(0, rz, 4001)
    integral = 2 * trapz(window(V, t_r, bk, ys, dh, R), ys) / math.sin(math.radians(theta))
    return lam * P_ign * (integral / 1000) / 3.156e7


# ---------- агрегированный расчёт ----------
def compute_all(cfg):
    """cfg — dict. Возвращает dict с результатами (числа, таблицы)."""
    I_thr = cfg['I_threshold_kW_m2']
    D_main_mm = cfg['D_main_mm']
    p_MPa = cfg['p_MPa']
    k_t_list = cfg['k_t_list']
    V_kmh = cfg['V_kmh']
    V_to_VS = cfg['V_to_VS']
    n_structural = cfg['n_structural']
    bank_main_deg = cfg['bank_main_deg']
    bank_list_deg = cfg['bank_list_deg']
    t_vis = cfg['t_react_visual_s']
    t_atc = cfg['t_react_atc_s']
    materials = cfg['materials']
    D_kr_equipment = cfg['D_kr_equipment']
    main_material = cfg['main_material']
    lam = cfg['lambda_rupture_per_km_year']
    P_ign = cfg['P_ignition']
    theta_deg = cfg['theta_deg']
    dh_m = cfg['dh_m']
    flights = cfg['flights_per_year']
    glide_slope_deg = cfg['glide_slope_deg']
    threshold_height_m = cfg['threshold_height_m']
    H_center_m = cfg['H_center_m']
    escape_cases = cfg['escape_cases']

    V = V_kmh / 3.6
    V_S = V / V_to_VS

    D_kr_levels = {name: round(D_kr_material(m), -1) for name, m in materials.items()}
    D_kr_levels['оборудование'] = D_kr_equipment
    D_kr_main = D_kr_levels[main_material]

    n_main = n_allowed(V, V_S, bank_main_deg, n_structural)
    R_main = R_turn(V, n_main)
    bk_main = b_kr(D_kr_main, V, D_main_mm, p_MPa, I_thr=I_thr)

    summary_lines = []
    summary_lines.append(f'Газопровод {D_main_mm} мм, {p_MPa:g} МПа, V = {V_kmh:g} км/ч')
    r_p = r_pir(D_main_mm, p_MPa)
    summary_lines.append(f'  r_PIR = {r_p:.0f} м, доза при пролете на r_PIR = '
                         f'{dose_pass(r_p, V, D_main_mm, p_MPa, I_thr=I_thr):.0f} кДж/м²')
    for name, Dk in D_kr_levels.items():
        summary_lines.append(
            f'  b_кр ({name}, {Dk:.0f} кДж/м²): ' +
            ', '.join(f'k_t = {k}: {b_kr(Dk, V, D_main_mm, p_MPa, k, I_thr=I_thr):.0f} м'
                      for k in k_t_list))
    summary_lines.append(
        f'  перегрузка: по сваливанию {(V / V_S) ** 2:.2f}, по прочности {n_structural}, ' +
        ', '.join(f'крен {b}° -> {n_bank(b):.3f}' for b in bank_list_deg))
    for label, bank, n_fixed in escape_cases:
        n = n_bank(bank) if bank is not None else n_fixed
        R = R_turn(V, n)
        t_geom = math.sqrt(bk_main * (2 * R + bk_main)) / V
        summary_lines.append(
            f'  {label}: a = {a_lat(n):.1f} м/с², R = {R:.0f} м, t_геом = {t_geom:.1f} с')
    summary_lines.append(
        f'  d_обн (крен {bank_main_deg}°, t_р = {t_vis} с): ' +
        ', '.join(f'k_t = {k}: {d_obn(V, t_vis, b_kr(D_kr_main, V, D_main_mm, p_MPa, k, I_thr=I_thr), 0, R_main):.0f} м'
                  for k in k_t_list))
    for k in k_t_list:
        bk = b_kr(D_kr_main, V, D_main_mm, p_MPa, k, I_thr=I_thr)
        x_thr = max(bk + H_center_m - threshold_height_m, 0) / math.tan(math.radians(glide_slope_deg))
        summary_lines.append(f'  опасный участок глиссады (k_t = {k}): до {x_thr / 1000:.1f} км от порога')

    table3 = []
    for k in k_t_list:
        for name, Dk in D_kr_levels.items():
            bk = b_kr(Dk, V, D_main_mm, p_MPa, k, I_thr=I_thr)
            rz = math.sqrt(max(bk * bk - dh_m * dh_m, 0))
            T_vis = float(window(V, t_vis, bk, 0.0, dh_m, R_main))
            T_atc = float(window(V, t_atc, bk, 0.0, dh_m, R_main))
            P_vis = P_flight(V, t_vis, bk, dh_m, R_main, theta_deg, lam, P_ign)
            P_atc = P_flight(V, t_atc, bk, dh_m, R_main, theta_deg, lam, P_ign)
            table3.append(dict(
                D_kr=Dk, k_t=k, element=name, bk=bk,
                d_obn=d_obn(V, t_vis, rz, 0, R_main),
                T_vis=T_vis, T_atc=T_atc,
                P_vis=P_vis, P_atc=P_atc,
                F_vis=P_vis * flights, F_atc=P_atc * flights,
            ))

    return dict(
        V=V, V_S=V_S, D_kr_levels=D_kr_levels, D_kr_main=D_kr_main,
        n_main=n_main, R_main=R_main, bk_main=bk_main,
        summary_lines=summary_lines, table3=table3, params=cfg,
    )