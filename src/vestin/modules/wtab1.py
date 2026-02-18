# modules/wtab1.py
# Tab 1: Calculadora de juros compostos com gráfico de pizza.
# Equivalente a callbacks_tab1.h + callbacks_tab1_piechart.h do programa C.

import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDoubleSpinBox, QSpinBox, QComboBox, QLabel, QGroupBox, QSizePolicy,
    QScrollArea
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics

from vestin.modules.mathfin import ratepera_to_rateperm, calculates_total_and_final_amount


# ─────────────────────────────────────────────────────────────────────────────
# Widget gráfico de pizza — tamanho FIXO, sem redimensionamento
# ─────────────────────────────────────────────────────────────────────────────

class PieChartWidget(QWidget):

    PIE_H     = 300
    FSIZE_LEG = 14
    HPF       = 0.55   # fracção da largura para o círculo

    def __init__(self, values=None, labels=None, colors=None, parent=None):
        super().__init__(parent)
        self.values = list(values) if values else [0.0, 0.0]
        self.labels = list(labels) if labels else []
        self.colors = colors if colors else [
            QColor(127, 76, 178),
            QColor(76, 178, 127),
        ]
        self._update_size()

    # ── calcula PIE_W com base no texto mais largo ────────────────────────────
    def _update_size(self):
        font_leg = QFont("Sans", self.FSIZE_LEG)
        fm       = QFontMetrics(font_leg)

        # texto exemplo mais largo possível: "Label: 1,000,000.00"
        max_text_w = 0
        for i, val in enumerate(self.values):
            lbl  = self.labels[i] if i < len(self.labels) else ""
            text = f"{lbl}: {val:,.2f}" if lbl else f"{val:,.2f}"
            max_text_w = max(max_text_w, fm.horizontalAdvance(text))

        box_size  = self.FSIZE_LEG
        legend_w  = 8 + box_size + 4 + max_text_w + 8   # margem + box + gap + texto + margem
        circle_w  = int(legend_w / (1.0 - self.HPF))     # o círculo ocupa HPF da largura total
        pie_w     = max(300, circle_w)

        self.setFixedSize(pie_w, self.PIE_H)

    def set_values(self, values):
        self.values = list(values)
        self._update_size()   # recalcula largura se os números mudaram
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.PIE_H
        total = sum(self.values)
        if total <= 0:
            return

        cx     = w * self.HPF / 2.0
        cy     = h / 2.0
        radius = min(w * self.HPF / 2.0, h / 2.0) * 0.88

        # ── Fatias ────────────────────────────────────────────────────────────
        start_deg = 0.0
        for i, val in enumerate(self.values):
            span_deg = 360.0 * val / total
            color = self.colors[i] if i < len(self.colors) else QColor(180, 180, 180)
            painter.setBrush(color)
            painter.setPen(Qt.white)
            painter.drawPie(
                int(cx - radius), int(cy - radius),
                int(radius * 2),  int(radius * 2),
                int(start_deg * 16), int(span_deg * 16)
            )

            # Percentagem no centro da fatia
            mid_rad = math.radians(-(start_deg + span_deg / 2.0))
            tx = cx + radius * 0.60 * math.cos(mid_rad)
            ty = cy + radius * 0.60 * math.sin(mid_rad)

            fsize = max(7, int(radius / 6))
            font  = QFont("Sans", fsize)
            painter.setFont(font)
            painter.setPen(Qt.black)
            pct  = 100.0 * val / total
            text = f"{pct:.1f}%"
            fm   = QFontMetrics(font)
            tw   = fm.horizontalAdvance(text)
            painter.drawText(QPointF(tx - tw / 2.0, ty + fm.ascent() / 2.0), text)

            start_deg += span_deg

        # ── Legenda ───────────────────────────────────────────────────────────
        lx       = w * self.HPF + 8.0
        n        = len(self.values)
        font_leg = QFont("Sans", self.FSIZE_LEG)
        painter.setFont(font_leg)
        fm_leg   = QFontMetrics(font_leg)
        box_size = self.FSIZE_LEG
        step     = h / (n + 0.5)

        for i, val in enumerate(self.values):
            color   = self.colors[i] if i < len(self.colors) else QColor(180, 180, 180)
            line_cy = step * i + step * 0.5

            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(lx), int(line_cy - box_size / 2.0), box_size, box_size)

            lbl     = self.labels[i] if i < len(self.labels) else ""
            text    = f"{lbl}: {val:,.2f}" if lbl else f"{val:,.2f}"
            ty_text = line_cy + fm_leg.ascent() / 2.0 - fm_leg.descent() / 2.0
            painter.setPen(Qt.black)
            painter.drawText(QPointF(lx + box_size + 4.0, ty_text), text)


# ─────────────────────────────────────────────────────────────────────────────
# Tab1
# ─────────────────────────────────────────────────────────────────────────────
class Tab1Widget(QWidget):
    """
    Tab 1 — Juros compostos.

    Entradas : Quantia inicial, Aporte mensal, Taxa de juros, Período.
    Saídas   : Total aportado, Total de juros, Montante final + gráfico de pizza.
    """

    DEFAULT_TEXTS = {
        "tab_label":          "Compound Interest",
        "group_input":        "Parameters",
        "label_amount":       "Initial amount:",
        "label_contribution": "Monthly contribution:",
        "label_rate":         "Interest rate (%):",
        "rate_monthly":       "Monthly",
        "rate_annual":        "Annual",
        "label_period":       "Period:",
        "period_months":      "Months",
        "period_years":       "Years",
        "group_result":       "Results",
        "label_total":        "Total invested:",
        "label_interest":     "Total interest:",
        "label_final":        "Final amount:",
        "pie_label_total":    "Invested",
        "pie_label_interest": "Interest",
    }

    def __init__(self, texts=None, parent=None):
        super().__init__(parent)
        self.T = dict(self.DEFAULT_TEXTS)
        if texts:
            self.T.update(texts)
        self._build_ui()
        self._connect_signals()
        self._recalculate()

    # ── Construção da UI ─────────────────────────────────────────────────────
    def _build_ui(self):
        T    = self.T
        root = QHBoxLayout(self)

        # ── Painel esquerdo: inputs + resultados ─────────────────────────────
        left = QVBoxLayout()

        grp_in = QGroupBox(T["group_input"])
        form   = QFormLayout()

        self.spin_amount = QDoubleSpinBox()
        self.spin_amount.setRange(0, 1_000_000_000)
        self.spin_amount.setDecimals(2)
        self.spin_amount.setSingleStep(100)
        self.spin_amount.setValue(1000.0)
        form.addRow(T["label_amount"], self.spin_amount)

        self.spin_contribution = QDoubleSpinBox()
        self.spin_contribution.setRange(0, 1_000_000_000)
        self.spin_contribution.setDecimals(2)
        self.spin_contribution.setSingleStep(100)
        self.spin_contribution.setValue(500.0)
        form.addRow(T["label_contribution"], self.spin_contribution)

        rate_widget = QWidget()
        rate_row    = QHBoxLayout(rate_widget)
        rate_row.setContentsMargins(0, 0, 0, 0)
        self.spin_rate = QDoubleSpinBox()
        self.spin_rate.setRange(0, 10000)
        self.spin_rate.setDecimals(4)
        self.spin_rate.setSingleStep(0.1)
        self.spin_rate.setValue(1.0)
        self.combo_rate = QComboBox()
        self.combo_rate.addItems([T["rate_monthly"], T["rate_annual"]])
        rate_row.addWidget(self.spin_rate)
        rate_row.addWidget(self.combo_rate)
        form.addRow(T["label_rate"], rate_widget)

        period_widget = QWidget()
        period_row    = QHBoxLayout(period_widget)
        period_row.setContentsMargins(0, 0, 0, 0)
        self.spin_period = QSpinBox()
        self.spin_period.setRange(1, 9999)
        self.spin_period.setValue(12)
        self.combo_period = QComboBox()
        self.combo_period.addItems([T["period_months"], T["period_years"]])
        period_row.addWidget(self.spin_period)
        period_row.addWidget(self.combo_period)
        form.addRow(T["label_period"], period_widget)

        grp_in.setLayout(form)
        left.addWidget(grp_in)

        grp_res  = QGroupBox(T["group_result"])
        res_form = QFormLayout()

        def _result_label():
            lbl = QLabel("0.00")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            f = lbl.font(); f.setBold(True); lbl.setFont(f)
            return lbl

        self.lbl_total_amount   = _result_label()
        self.lbl_total_interest = _result_label()
        self.lbl_final_amount   = _result_label()
        res_form.addRow(T["label_total"],    self.lbl_total_amount)
        res_form.addRow(T["label_interest"], self.lbl_total_interest)
        res_form.addRow(T["label_final"],    self.lbl_final_amount)
        grp_res.setLayout(res_form)
        left.addWidget(grp_res)

        left.addStretch()
        left_widget = QWidget()
        left_widget.setLayout(left)
        #left_widget.setFixedWidth(300)
        root.addWidget(left_widget)

        # ── Painel direito: pie dentro de QScrollArea ─────────────────────────
        self.pie = PieChartWidget(
            values=[1000.0, 0.0],
            labels=[T["pie_label_total"], T["pie_label_interest"]]
        )

        scroll = QScrollArea()
        scroll.setWidget(self.pie)
        scroll.setWidgetResizable(False)   # widget tem tamanho fixo
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        root.addWidget(scroll)

    # ── Conexão de sinais ────────────────────────────────────────────────────
    def _connect_signals(self):
        self.spin_amount.valueChanged.connect(self._recalculate)
        self.spin_contribution.valueChanged.connect(self._recalculate)
        self.spin_rate.valueChanged.connect(self._recalculate)
        self.combo_rate.currentIndexChanged.connect(self._recalculate)
        self.spin_period.valueChanged.connect(self._recalculate)
        self.combo_period.currentIndexChanged.connect(self._recalculate)

    # ── Cálculo principal ────────────────────────────────────────────────────
    def _recalculate(self):
        amount       = self.spin_amount.value()
        contribution = self.spin_contribution.value()
        rate         = self.spin_rate.value()
        period       = self.spin_period.value()

        if self.combo_rate.currentIndex() == 1:
            rate = ratepera_to_rateperm(rate)

        if self.combo_period.currentIndex() == 1:
            period = period * 12

        total_amount, final_amount = calculates_total_and_final_amount(
            amount, contribution, rate, period
        )
        total_interest = final_amount - total_amount

        self.lbl_total_amount.setText(f"{total_amount:,.2f}")
        self.lbl_total_interest.setText(f"{total_interest:,.2f}")
        self.lbl_final_amount.setText(f"{final_amount:,.2f}")

        self.pie.set_values([total_amount, total_interest])

    # ── Serialização para save/load ──────────────────────────────────────────
    def get_data(self):
        return {
            "initial_amount":       self.spin_amount.value(),
            "monthly_contribution": self.spin_contribution.value(),
            "rate":                 self.spin_rate.value(),
            "rate_type":            self.combo_rate.currentIndex(),
            "period":               self.spin_period.value(),
            "period_type":          self.combo_period.currentIndex(),
        }

    def set_data(self, data):
        if "initial_amount"       in data: self.spin_amount.setValue(data["initial_amount"])
        if "monthly_contribution" in data: self.spin_contribution.setValue(data["monthly_contribution"])
        if "rate"                 in data: self.spin_rate.setValue(data["rate"])
        if "rate_type"            in data: self.combo_rate.setCurrentIndex(data["rate_type"])
        if "period"               in data: self.spin_period.setValue(data["period"])
        if "period_type"          in data: self.combo_period.setCurrentIndex(data["period_type"])
