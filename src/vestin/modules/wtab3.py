# modules/wtab3.py
# Tab 3: Conversor de taxas de juros.
# Equivalente a callbacks_tab3.h do programa C.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QDoubleSpinBox, QGroupBox, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt

from vestin.modules.mathfin import (
    rateperm_to_ratepera,
    ratepera_to_rateperm,
    rateperm_to_rateperxm,
    rateperxm_to_rateperm,
)


class Tab3Widget(QWidget):
    """
    Tab 3 — Conversor de taxas.

    Secção A : Taxa mensal ↔ Taxa anual  (equivalente).
    Secção B : Taxa mensal + X meses  →  Taxa acumulada em X meses  (e vice-versa).
    """

    # Textos padrão — podem ser sobrescritos via CONFIG
    DEFAULT_TEXTS = {
        "tab_label":          "Rate Converter",
        "group_ma":           "Monthly ↔ Annual",
        "label_monthly":      "Monthly rate (%):",
        "label_annual":       "Annual rate (%):",
        "group_xm":           "Rate over X months",
        "label_rate_m":       "Monthly rate (%):",
        "label_months":       "Number of months:",
        "label_rate_xm":      "Rate over X months (%):",
    }

    def __init__(self, texts=None, parent=None):
        super().__init__(parent)
        self.T = dict(self.DEFAULT_TEXTS)
        if texts:
            self.T.update(texts)
        self._build_ui()
        self._connect_signals()

    # ── Construção da UI ─────────────────────────────────────────────────────
    def _build_ui(self):
        T = self.T
        root = QVBoxLayout(self)

        # ── Secção A: Mensal ↔ Anual ─────────────────────────────────────────
        grp_ma = QGroupBox(T["group_ma"])
        form_ma = QFormLayout()

        self.spin_rm = QDoubleSpinBox()
        self.spin_rm.setRange(0, 10000)
        self.spin_rm.setDecimals(6)
        self.spin_rm.setSingleStep(0.1)
        self.spin_rm.setValue(1.0)
        form_ma.addRow(T["label_monthly"], self.spin_rm)

        self.spin_ra = QDoubleSpinBox()
        self.spin_ra.setRange(0, 10000)
        self.spin_ra.setDecimals(6)
        self.spin_ra.setSingleStep(1.0)
        self.spin_ra.setValue(rateperm_to_ratepera(1.0))
        form_ma.addRow(T["label_annual"], self.spin_ra)

        grp_ma.setLayout(form_ma)
        root.addWidget(grp_ma)

        # ── Secção B: Taxa por X meses ───────────────────────────────────────
        grp_xm = QGroupBox(T["group_xm"])
        form_xm = QFormLayout()

        self.spin_rate_m = QDoubleSpinBox()
        self.spin_rate_m.setRange(0, 10000)
        self.spin_rate_m.setDecimals(6)
        self.spin_rate_m.setSingleStep(0.1)
        self.spin_rate_m.setValue(1.0)
        form_xm.addRow(T["label_rate_m"], self.spin_rate_m)

        self.spin_meses = QDoubleSpinBox()
        self.spin_meses.setRange(1, 9999)
        self.spin_meses.setDecimals(0)
        self.spin_meses.setSingleStep(1)
        self.spin_meses.setValue(12)
        form_xm.addRow(T["label_months"], self.spin_meses)

        self.spin_rate_xm = QDoubleSpinBox()
        self.spin_rate_xm.setRange(0, 10000)
        self.spin_rate_xm.setDecimals(6)
        self.spin_rate_xm.setSingleStep(1.0)
        self.spin_rate_xm.setValue(
            rateperm_to_rateperxm(1.0, 12)
        )
        form_xm.addRow(T["label_rate_xm"], self.spin_rate_xm)

        grp_xm.setLayout(form_xm)
        root.addWidget(grp_xm)

        root.addStretch()

    # ── Conexão de sinais ────────────────────────────────────────────────────
    def _connect_signals(self):
        self.spin_rm.valueChanged.connect(self._on_rm_changed)
        self.spin_ra.valueChanged.connect(self._on_ra_changed)
        self.spin_rate_m.valueChanged.connect(self._on_rate_m_or_meses_changed)
        self.spin_meses.valueChanged.connect(self._on_rate_m_or_meses_changed)
        self.spin_rate_xm.valueChanged.connect(self._on_rate_xm_changed)

    # ── Callbacks ────────────────────────────────────────────────────────────
    def _on_rm_changed(self, rpm):
        """Mensal alterada → atualiza Anual."""
        self.spin_ra.blockSignals(True)
        self.spin_ra.setValue(rateperm_to_ratepera(rpm))
        self.spin_ra.blockSignals(False)

    def _on_ra_changed(self, rpa):
        """Anual alterada → atualiza Mensal."""
        self.spin_rm.blockSignals(True)
        self.spin_rm.setValue(ratepera_to_rateperm(rpa))
        self.spin_rm.blockSignals(False)

    def _on_rate_m_or_meses_changed(self):
        """Taxa mensal (B) ou nº meses alterado → recalcula taxa em X meses."""
        rm  = self.spin_rate_m.value()
        m   = self.spin_meses.value()
        rxm = rateperm_to_rateperxm(rm, m)
        self.spin_rate_xm.blockSignals(True)
        self.spin_rate_xm.setValue(rxm)
        self.spin_rate_xm.blockSignals(False)

    def _on_rate_xm_changed(self, rxm):
        """Taxa em X meses alterada → recalcula taxa mensal (B)."""
        m  = self.spin_meses.value()
        rm = rateperxm_to_rateperm(rxm, m)
        self.spin_rate_m.blockSignals(True)
        self.spin_rate_m.setValue(rm)
        self.spin_rate_m.blockSignals(False)

    # ── Serialização para save/load ──────────────────────────────────────────
    def get_data(self):
        """Retorna dict com os dados do tab (para salvar em JSON)."""
        return {
            "monthly_rate":  self.spin_rm.value(),
            "annual_rate":   self.spin_ra.value(),
            "rate_m":        self.spin_rate_m.value(),
            "xmonths":       self.spin_meses.value(),
            "xrate":         self.spin_rate_xm.value(),
        }

    def set_data(self, data):
        """Preenche os campos a partir de um dict (carregado de JSON)."""
        if "monthly_rate" in data: self.spin_rm.setValue(data["monthly_rate"])
        if "annual_rate"  in data: self.spin_ra.setValue(data["annual_rate"])
        if "rate_m"       in data: self.spin_rate_m.setValue(data["rate_m"])
        if "xmonths"      in data: self.spin_meses.setValue(data["xmonths"])
        if "xrate"        in data: self.spin_rate_xm.setValue(data["xrate"])
