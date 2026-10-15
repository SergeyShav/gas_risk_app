# ui/params_panel.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLineEdit,
    QScrollArea, QComboBox, QLabel
)


DEFAULTS = {
    'D_list_mm': '530, 720, 820, 1020, 1220, 1420',
    'D_main_mm': '1420',
    'p_MPa': '7.4',
    'I_threshold_kW_m2': '15.8',
    'k_t_list': '1, 3',
    'V_kmh': '250',
    'V_to_VS': '1.3',
    'n_structural': '2.0',
    'bank_main_deg': '30',
    'bank_list_deg': '15, 30',
    't_react_visual_s': '6',
    't_react_atc_s': '60',
    'D_kr_equipment': '3300',
    'lambda_rupture_per_km_year': '2.0e-5',
    'P_ignition': '0.423',
    'theta_deg': '90',
    'dh_m': '0',
    'flights_per_year': '1e5',
    'glide_slope_deg': '3',
    'threshold_height_m': '15',
    'H_center_m': '0',
}


class ParamsPanel(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        self.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setSpacing(10)

        self.fields = {}

        # --- Газопровод ---
        gb1 = QGroupBox('Газопровод')
        f1 = QFormLayout(gb1)
        self._add(f1, 'D_list_mm', 'Диаметры для графиков, мм')
        self._add(f1, 'D_main_mm', 'D основной (сводка), мм')
        self._add(f1, 'p_MPa', 'Давление, МПа')
        self._add(f1, 'I_threshold_kW_m2', 'I_порог, кВт/м²')
        self._add(f1, 'k_t_list', 'k_t (список через запятую)')
        lay.addWidget(gb1)

        # --- ВС ---
        gb2 = QGroupBox('Воздушное судно')
        f2 = QFormLayout(gb2)
        self._add(f2, 'V_kmh', 'Скорость, км/ч')
        self._add(f2, 'V_to_VS', 'V / V_S')
        self._add(f2, 'n_structural', 'n_structural')
        self._add(f2, 'bank_main_deg', 'Крен основной, °')
        self._add(f2, 'bank_list_deg', 'Крены для графиков, ° (через запятую)')
        self._add(f2, 't_react_visual_s', 't_реакц. визуально, с')
        self._add(f2, 't_react_atc_s', 't_реакц. УВД, с')
        lay.addWidget(gb2)

        # --- Материалы ---
        gb3 = QGroupBox('Материалы обшивки')
        f3 = QFormLayout(gb3)
        self._add(f3, 'D_kr_equipment', 'D_кр оборудование, кДж/м²')

        self.combo_main = QComboBox()
        self.combo_main.addItems(['ПКМ', 'сплав Д16'])
        self.combo_main.setCurrentText('сплав Д16')
        f3.addRow(QLabel('Основной материал (для рис. 2, 4, 5)'), self.combo_main)

        note = QLabel(
            'Свойства материалов заданы в коде:\n'
            '  ПКМ:  ρ=1600, c=1000, δ=2.0 мм, ΔT=100 K\n'
            '  Д16:  ρ=2780, c=900,  δ=1.6 мм, ΔT=150 K'
        )
        note.setStyleSheet('color: gray; font-size: 10px;')
        f3.addRow(note)
        lay.addWidget(gb3)

        # --- Вероятности и геометрия ---
        gb4 = QGroupBox('Вероятности и геометрия')
        f4 = QFormLayout(gb4)
        self._add(f4, 'lambda_rupture_per_km_year', 'λ разрывов, 1/(км·год)')
        self._add(f4, 'P_ignition', 'P воспламенения')
        self._add(f4, 'theta_deg', 'θ пересечения, °')
        self._add(f4, 'dh_m', 'Δh над центром, м')
        self._add(f4, 'flights_per_year', 'Полётов в год')
        self._add(f4, 'glide_slope_deg', 'Глиссада, °')
        self._add(f4, 'threshold_height_m', 'Высота порога, м')
        self._add(f4, 'H_center_m', 'Высота центра, м')
        lay.addWidget(gb4)

        lay.addStretch(1)

    def _add(self, form: QFormLayout, key: str, label: str):
        le = QLineEdit(DEFAULTS[key])
        le.setMinimumWidth(180)
        self.fields[key] = le
        form.addRow(QLabel(label), le)

    # ---------- парсинг ----------
    def _parse_float(self, le: QLineEdit) -> float:
        txt = le.text().strip().replace(',', '.')
        return float(txt)

    def _parse_list_float(self, le: QLineEdit):
        txt = le.text().strip()
        if not txt:
            return []
        parts = [p.strip().replace(',', '.') for p in txt.replace(';', ',').split(',')]
        return [float(p) for p in parts if p]

    def _parse_list_int(self, le: QLineEdit):
        return [int(round(x)) for x in self._parse_list_float(le)]

    def collect(self) -> dict:
        """Собирает все поля в cfg-dict. Кидает ValueError с понятным текстом."""
        f = self.fields

        try:
            cfg = dict(
                D_list_mm=self._parse_list_float(f['D_list_mm']),
                D_main_mm=self._parse_float(f['D_main_mm']),
                p_MPa=self._parse_float(f['p_MPa']),
                I_threshold_kW_m2=self._parse_float(f['I_threshold_kW_m2']),
                k_t_list=self._parse_list_int(f['k_t_list']),
                V_kmh=self._parse_float(f['V_kmh']),
                V_to_VS=self._parse_float(f['V_to_VS']),
                n_structural=self._parse_float(f['n_structural']),
                bank_main_deg=self._parse_float(f['bank_main_deg']),
                bank_list_deg=self._parse_list_float(f['bank_list_deg']),
                t_react_visual_s=self._parse_float(f['t_react_visual_s']),
                t_react_atc_s=self._parse_float(f['t_react_atc_s']),
                D_kr_equipment=self._parse_float(f['D_kr_equipment']),
                lambda_rupture_per_km_year=self._parse_float(f['lambda_rupture_per_km_year']),
                P_ignition=self._parse_float(f['P_ignition']),
                theta_deg=self._parse_float(f['theta_deg']),
                dh_m=self._parse_float(f['dh_m']),
                flights_per_year=self._parse_float(f['flights_per_year']),
                glide_slope_deg=self._parse_float(f['glide_slope_deg']),
                threshold_height_m=self._parse_float(f['threshold_height_m']),
                H_center_m=self._parse_float(f['H_center_m']),
            )
        except Exception as e:
            raise ValueError(f'Ошибка в поле ввода: {e}')

        # материалы и main_material
        cfg['materials'] = {
            'ПКМ': dict(rho=1600, c=1000, delta_mm=2.0, dT_K=100, alpha=1.0),
            'сплав Д16': dict(rho=2780, c=900, delta_mm=1.6, dT_K=150, alpha=1.0),
        }
        cfg['main_material'] = self.combo_main.currentText()

        # escape_cases фиксированы
        cfg['escape_cases'] = [
            ('крен 15°', 15, None),
            ('крен 30°', 30, None),
            ('n_y = 1,5', None, 1.5),
            ('n_y = 2,0', None, 2.0),
        ]
        return cfg