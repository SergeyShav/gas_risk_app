# ui/main_window.py
import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSplitter, QMessageBox, QLabel
)

import calc
from ui.params_panel import ParamsPanel
from ui.results_panel import ResultsPanel
from ui.plots_panel import PlotsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Риск ВС от теплового излучения пожара на газопроводе')
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # ---- Левая часть: параметры + кнопки ----
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel('⚙️  Параметры расчёта')
        title.setStyleSheet('font-weight: bold; padding: 6px; font-size: 13px;')
        left_lay.addWidget(title)

        self.params = ParamsPanel()
        left_lay.addWidget(self.params, 1)

        self.btn_calc = QPushButton('▶  Расчёт')
        self.btn_calc.setMinimumHeight(38)
        self.btn_calc.clicked.connect(self.on_calc)
        left_lay.addWidget(self.btn_calc)

        self.btn_plots = QPushButton('📈  Построить графики')
        self.btn_plots.setMinimumHeight(38)
        self.btn_plots.clicked.connect(self.on_plots)
        self.btn_plots.setEnabled(False)
        left_lay.addWidget(self.btn_plots)

        left.setMinimumWidth(340)
        left.setMaximumWidth(480)

        # ---- Правая часть: результаты / графики ----
        self.right_tabs = ResultsPanel()
        self.plots_panel = PlotsPanel()
        # Вставляем реальный PlotsPanel на место заглушки
        self.right_tabs.removeTab(2)
        self.right_tabs.insertTab(2, self.plots_panel, 'Графики')

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.right_tabs)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

        self._last_result = None
        self._last_cfg = None

    # ---------- обработчики ----------
    def on_calc(self):
        try:
            cfg = self.params.collect()
        except ValueError as e:
            QMessageBox.warning(self, 'Ошибка ввода', str(e))
            return

        try:
            res = calc.compute_all(cfg)
        except Exception:
            QMessageBox.critical(self, 'Ошибка расчёта',
                                 'Не удалось выполнить расчёт:\n\n' + traceback.format_exc())
            return

        self._last_result = res
        self._last_cfg = cfg

        self.right_tabs.set_summary(res['summary_lines'])
        self.right_tabs.set_table3(res['table3'])
        self.right_tabs.setCurrentIndex(0)

        self.btn_plots.setEnabled(True)

    def on_plots(self):
        if self._last_result is None:
            QMessageBox.information(self, 'Нет данных',
                                    'Сначала выполните расчёт.')
            return
        try:
            self.plots_panel.rebuild(self._last_result)
        except Exception:
            QMessageBox.critical(self, 'Ошибка построения',
                                 'Не удалось построить графики:\n\n' + traceback.format_exc())
            return
        self.right_tabs.setCurrentIndex(2)