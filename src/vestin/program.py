import os
import sys
import signal

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLabel, QWidget,
    QSizePolicy, QAction, QTabWidget, QStatusBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QDesktopServices


import vestin.about as about
import vestin.modules.configure as configure
from vestin.modules.resources import resource_path

from vestin.modules.wabout import show_about_window
from vestin.modules.wtab1  import Tab1Widget
from vestin.modules.wtab3  import Tab3Widget
from vestin.desktop import create_desktop_file, create_desktop_directory, create_desktop_menu


# ---------- Path to config file ----------
CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    ".config",
    about.__package__,
    "config.json"
)

DEFAULT_CONTENT = {
    # ── Toolbar ──────────────────────────────────────────────────────────────
    "toolbar_configure":         "Configure",
    "toolbar_configure_tooltip": "Open the program GUI JSON configuration file",
    "toolbar_about":             "About",
    "toolbar_about_tooltip":     "About the program",
    "toolbar_coffee":            "Coffee",
    "toolbar_coffee_tooltip":    "Buy me a coffee (TrucomanX)",
    # ── Window ───────────────────────────────────────────────────────────────
    "window_width":  1024,
    "window_height": 400,
    # ── Status bar ───────────────────────────────────────────────────────────
    "status_ready": "Ready.",
    # ── Tab labels ───────────────────────────────────────────────────────────
    "tab1_label": "Compound Interest",
    "tab3_label": "Rate Converter",
    # ── Tab1 texts ───────────────────────────────────────────────────────────
    "tab1_group_input":        "Parameters",
    "tab1_label_amount":       "Initial amount:",
    "tab1_label_contribution": "Monthly contribution:",
    "tab1_label_rate":         "Interest rate (%):",
    "tab1_rate_monthly":       "Monthly",
    "tab1_rate_annual":        "Annual",
    "tab1_label_period":       "Period:",
    "tab1_period_months":      "Months",
    "tab1_period_years":       "Years",
    "tab1_group_result":       "Results",
    "tab1_label_total":        "Total invested:",
    "tab1_label_interest":     "Total interest:",
    "tab1_label_final":        "Final amount:",
    "tab1_pie_label_total":    "Invested",
    "tab1_pie_label_interest": "Interest",
    # ── Tab3 texts ───────────────────────────────────────────────────────────
    "tab3_group_ma":      "Monthly ↔ Annual",
    "tab3_label_monthly": "Monthly rate (%):",
    "tab3_label_annual":  "Annual rate (%):",
    "tab3_group_xm":      "Rate over X months",
    "tab3_label_rate_m":  "Monthly rate (%):",
    "tab3_label_months":  "Number of months:",
    "tab3_label_rate_xm": "Rate over X months (%):",
}


configure.verify_default_config(CONFIG_PATH, default_content=DEFAULT_CONTENT)
CONFIG = configure.load_config(CONFIG_PATH)

# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH = os.path.join(
    os.path.expanduser("~"),
    ".config",
    about.__package__,
    "data.json"
)

DEFAULT_DATA = {
    "tab1": {},
    "tab3": {},
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(about.__program_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])

        self.icon_path = resource_path("icons", "logo.png")
        self.setWindowIcon(QIcon(self.icon_path))

        self._create_statusbar()
        self._create_toolbar()
        self._generate_ui()
        self._load_data()

    # ── Status bar ───────────────────────────────────────────────────────────
    def _create_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(CONFIG["status_ready"])

    # ── UI principal ─────────────────────────────────────────────────────────
    def _generate_ui(self):
        # Notebook (QTabWidget)
        self.notebook = QTabWidget()

        # Tab1 — Juros compostos
        tab1_texts = {k[5:]: v for k, v in CONFIG.items() if k.startswith("tab1_")}
        self.tab1 = Tab1Widget(texts=tab1_texts)
        self.notebook.addTab(self.tab1, CONFIG["tab1_label"])

        # Tab3 — Conversor de taxas
        tab3_texts = {k[5:]: v for k, v in CONFIG.items() if k.startswith("tab3_")}
        self.tab3 = Tab3Widget(texts=tab3_texts)
        self.notebook.addTab(self.tab3, CONFIG["tab3_label"])

        self.setCentralWidget(self.notebook)

    # ── Toolbar ──────────────────────────────────────────────────────────────
    def _create_toolbar(self):
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.toolbar_spacer = QWidget()
        self.toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar.addWidget(self.toolbar_spacer)

        configure_path = resource_path("icons", "text-configure.png")
        self.configure_action = QAction(
            QIcon(configure_path),
            CONFIG["toolbar_configure"], self
        )
        self.configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        self.configure_action.triggered.connect(self.open_configure_editor)
        self.toolbar.addAction(self.configure_action)

        about_path = resource_path("icons", "status_help.png")
        self.about_action = QAction(
            QIcon(about_path),
            CONFIG["toolbar_about"], self
        )
        self.about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        self.about_action.triggered.connect(self.open_about)
        self.toolbar.addAction(self.about_action)

        coffee_path = resource_path("icons", "emote-love.png")
        self.coffee_action = QAction(
            QIcon(coffee_path),
            CONFIG["toolbar_coffee"], self
        )
        self.coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        self.coffee_action.triggered.connect(self.on_coffee_action_click)
        self.toolbar.addAction(self.coffee_action)

        self.toolbar.orientationChanged.connect(self.on_update_spacer_policy)
        self.on_update_spacer_policy()

    def on_update_spacer_policy(self):
        if self.toolbar.orientation() == Qt.Horizontal:
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        else:
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    # ── Save / Load de dados ─────────────────────────────────────────────────
    def _save_data(self):
        data = {
            "tab1": self.tab1.get_data(),
            "tab3": self.tab3.get_data(),
        }
        configure.save_config(DATA_PATH, data)
        self.status_bar.showMessage(f"Saved: {DATA_PATH}")

    def _load_data(self):
        data = configure.load_config(DATA_PATH, default_content=DEFAULT_DATA)
        self.tab1.set_data(data.get("tab1", {}))
        self.tab3.set_data(data.get("tab3", {}))
        self.status_bar.showMessage(f"Loaded: {DATA_PATH}")

    # ── Acções ───────────────────────────────────────────────────────────────
    def _open_file_in_text_editor(self, filepath):
        import subprocess
        if os.name == 'nt':
            os.startfile(filepath)
        else:
            subprocess.run(['xdg-open', filepath])

    def open_configure_editor(self):
        self._open_file_in_text_editor(CONFIG_PATH)

    def open_about(self):
        data = {
            "version":      about.__version__,
            "package":      about.__package__,
            "program_name": about.__program_name__,
            "author":       about.__author__,
            "email":        about.__email__,
            "description":  about.__description__,
            "url_source":   about.__url_source__,
            "url_doc":      about.__url_doc__,
            "url_funding":  about.__url_funding__,
            "url_bugs":     about.__url_bugs__,
        }
        show_about_window(data, self.icon_path)

    def on_coffee_action_click(self):
        from PyQt5.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))

    # ── Fechar janela → salvar dados ─────────────────────────────────────────
    def closeEvent(self, event):
        self._save_data()
        super().closeEvent(event)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_name__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return

    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
