# ui/results_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont


class ResultsPanel(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Сводка ---
        self.txt_summary = QTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_summary.setFont(QFont('Consolas', 10))
        self.addTab(self.txt_summary, 'Сводка')

        # --- Таблица 3 ---
        self.table = QTableWidget()
        self.addTab(self.table, 'Таблица 3')

        # --- Графики (пустой placeholder, заполнит PlotsPanel) ---
        self.plots_placeholder = QWidget()
        self.addTab(self.plots_placeholder, 'Графики')

    def set_summary(self, lines):
        self.txt_summary.setPlainText('\n'.join(lines))

    def set_table3(self, rows):
        headers = ['D_кр', 'k_t', 'элемент', 'b_кр, м', 'd_обн, м',
                   'T_н виз., с', 'T_н УВД, с',
                   'P_пол виз.', 'P_пол УВД',
                   'F виз., 1/год', 'F УВД, 1/год']
        keys = ['D_kr', 'k_t', 'element', 'bk', 'd_obn',
                'T_vis', 'T_atc', 'P_vis', 'P_atc', 'F_vis', 'F_atc']

        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)

        def fmt(v):
            if isinstance(v, float):
                if v == 0:
                    return '0'
                a = abs(v)
                if a < 1e-3 or a >= 1e4:
                    return f'{v:.2e}'.replace('.', ',')
                return f'{v:.2f}'.replace('.', ',')
            return str(v)

        for i, row in enumerate(rows):
            for j, k in enumerate(keys):
                item = QTableWidgetItem(fmt(row[k]))
                self.table.setItem(i, j, item)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def show_plots_tab(self):
        self.setCurrentIndex(2)