from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMessageBox, QCheckBox,
    QGridLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication
from database.repository import ProviderRepository
from providers import get_provider
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


def setup_page_animation(widget: QWidget):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(280)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._page_entrance_anim = anim


def format_number(val: int) -> str:
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f}k"
    return str(val)


class ProviderTestWorker(QThread):
    finished_signal = Signal(str, int, bool, str, list)

    def __init__(self, provider_name, api_key, slot, db_manager):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.slot = slot
        self.db_manager = db_manager

    def run(self):
        provider = None
        try:
            provider = get_provider(self.provider_name, self.api_key)
            is_valid = provider.test_key()
            if is_valid:
                models = provider.discover_models()
                self.finished_signal.emit(self.provider_name, self.slot, True, "Connected & Verified", models or [])
            else:
                self.finished_signal.emit(self.provider_name, self.slot, False, provider.get_status(), [])
        except Exception as e:
            self.finished_signal.emit(self.provider_name, self.slot, False, f"Error: {str(e)}", [])
        finally:
            if provider:
                provider.close()


class SlotWidget(QFrame):
    def __init__(self, provider_name: str, slot: int, slot_data: dict, on_test, on_remove, on_manage_models, parent=None):
        super().__init__(parent)
        self.provider_name = provider_name
        self.slot = slot
        self.slot_data = slot_data
        self.on_test = on_test
        self.on_remove = on_remove
        self.on_manage_models = on_manage_models

        self.setStyleSheet("""
            SlotWidget {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Top line: Enable switch, Slot Label, Status Badge
        top_line = QHBoxLayout()
        top_line.setSpacing(10)

        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(slot_data.get("enabled", 1) == 1)
        self.enable_cb.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #334155;
                background-color: #131b2a;
            }
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
            }
        """)
        top_line.addWidget(self.enable_cb)

        slot_title = f"Slot {slot} • {'Production Primary' if slot == 1 else 'Secondary Failover'}"
        title_lbl = QLabel(slot_title)
        title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        top_line.addWidget(title_lbl)

        route_type = "Default Routing" if slot == 1 else "Failover Target"
        rt_lbl = QLabel(route_type)
        rt_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 10px; background-color: #131b2a; border: 1px solid #1e293b; border-radius: 4px; padding: 2px 6px;")
        top_line.addWidget(rt_lbl)

        top_line.addStretch()

        status_text = slot_data.get("status", "Not Configured")
        self.status_badge = QLabel(status_text)
        self.update_status_badge(status_text)
        top_line.addWidget(self.status_badge)

        layout.addLayout(top_line)

        # Inputs Grid: Label & API Secret Key
        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(12)

        # Custom Label
        name_box = QVBoxLayout()
        name_box.setSpacing(4)
        n_lbl = QLabel("Custom Key Label")
        n_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        name_box.addWidget(n_lbl)

        self.name_input = QLineEdit()
        self.name_input.setText(slot_data.get("display_name") or f"{provider_name}-Key-{slot}")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 6px 10px;
            }
            QLineEdit:focus {
                border-color: #2196f3;
            }
        """)
        name_box.addWidget(self.name_input)
        inputs_row.addLayout(name_box, stretch=1)

        # Secret Key with eye toggle & copy
        key_box = QVBoxLayout()
        key_box.setSpacing(4)

        k_head = QHBoxLayout()
        k_lbl = QLabel("API Secret Key")
        k_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        k_head.addWidget(k_lbl)
        k_head.addStretch()

        last_tested = slot_data.get("last_tested") or "Never tested"
        self.tested_lbl = QLabel(f"Last tested: {last_tested[:19] if len(last_tested) > 19 else last_tested}")
        self.tested_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 10px; background: transparent; border: none;")
        k_head.addWidget(self.tested_lbl)
        key_box.addLayout(k_head)

        key_frame = QFrame()
        key_frame.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QFrame:focus-within {
                border-color: #2196f3;
            }
        """)
        kf_lay = QHBoxLayout(key_frame)
        kf_lay.setContentsMargins(10, 0, 6, 0)
        kf_lay.setSpacing(4)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key = slot_data.get("api_key", "")
        if api_key and api_key != "••••••••":
            self.key_input.setText("••••••••")
        elif api_key:
            self.key_input.setText(api_key)

        self.key_input.setPlaceholderText("Enter provider API secret key...")
        self.key_input.setStyleSheet("background: transparent; border: none; color: #f1f5f9; font-family: 'JetBrains Mono', monospace; font-size: 12px; padding: 6px 0;")
        kf_lay.addWidget(self.key_input)

        self.show_key_btn = QPushButton()
        self.show_key_btn.setIcon(get_svg_icon("visibility" if "visibility" in get_svg_icon.__name__ else "description", "#94a3b8", 14))
        self.show_key_btn.setFixedSize(22, 22)
        self.show_key_btn.setStyleSheet("background: transparent; border: none;")
        self.show_key_btn.setToolTip("Toggle Visibility")
        self.show_key_btn.clicked.connect(self.toggle_password_visibility)
        kf_lay.addWidget(self.show_key_btn)

        copy_btn = QPushButton()
        copy_btn.setIcon(get_svg_icon("content_copy", "#94a3b8", 14))
        copy_btn.setFixedSize(22, 22)
        copy_btn.setStyleSheet("background: transparent; border: none;")
        copy_btn.setToolTip("Copy API Key")
        copy_btn.clicked.connect(self.copy_key)
        kf_lay.addWidget(copy_btn)

        key_box.addWidget(key_frame)
        inputs_row.addLayout(key_box, stretch=2)

        layout.addLayout(inputs_row)

        # Bottom Actions Bar
        actions_bar = QHBoxLayout()
        actions_bar.setSpacing(10)

        # Models badge
        key_id = slot_data.get("id")
        self.models_lbl = QLabel()
        self.models_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        actions_bar.addWidget(self.models_lbl)
        actions_bar.addStretch()

        if key_id:
            manage_models_btn = QPushButton(" Manage Models")
            manage_models_btn.setIcon(get_svg_icon("tune", "#94a3b8", 12))
            manage_models_btn.setStyleSheet("""
                QPushButton {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                    color: #f1f5f9;
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    border-color: #2196f3;
                }
            """)
            manage_models_btn.clicked.connect(lambda: self.on_manage_models(key_id, slot))
            actions_bar.addWidget(manage_models_btn)

            remove_btn = QPushButton(" Remove")
            remove_btn.setIcon(get_svg_icon("delete", "#94a3b8", 12))
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                    color: #94a3b8;
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: rgba(239, 68, 68, 0.15);
                    border-color: rgba(239, 68, 68, 0.4);
                    color: #f87171;
                }
            """)
            remove_btn.clicked.connect(lambda: self.on_remove(self.provider_name, slot, key_id))
            actions_bar.addWidget(remove_btn)

        self.test_btn = QPushButton(" Test && Save")
        self.test_btn.setIcon(get_svg_icon("sync", "#ffffff", 12))
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.test_btn.clicked.connect(self.trigger_test)
        actions_bar.addWidget(self.test_btn)

        layout.addLayout(actions_bar)

    def update_status_badge(self, text: str):
        if "Valid" in text or "Connected" in text:
            self.status_badge.setText(" Connected & Verified")
            self.status_badge.setStyleSheet("""
                color: #4edea3;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(78, 222, 163, 0.1);
                border: 1px solid rgba(78, 222, 163, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
            """)
        elif "Testing" in text:
            self.status_badge.setText(" Testing Connection...")
            self.status_badge.setStyleSheet("""
                color: #fbbf24;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(251, 191, 36, 0.1);
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
            """)
        elif "Invalid" in text or "Error" in text:
            self.status_badge.setText(f" {text}")
            self.status_badge.setStyleSheet("""
                color: #f87171;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
            """)
        else:
            self.status_badge.setText(" Not Configured")
            self.status_badge.setStyleSheet("""
                color: #64748b;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 2px 8px;
            """)

    def toggle_password_visibility(self):
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def copy_key(self):
        key = self.key_input.text().strip()
        if key == "••••••••":
            key = self.slot_data.get("api_key", "")
        if key and key != "••••••••":
            QGuiApplication.clipboard().setText(key)

    def trigger_test(self):
        key = self.key_input.text().strip()
        disp_name = self.name_input.text().strip()
        enabled = 1 if self.enable_cb.isChecked() else 0

        if not key:
            QMessageBox.warning(self, "Error", "API Key cannot be empty.")
            return

        real_key = key
        if key == "••••••••":
            real_key = self.slot_data.get("api_key", "")

        if not real_key or real_key == "••••••••":
            QMessageBox.warning(self, "Error", "Cannot test masked key without entering it first.")
            return

        self.test_btn.setEnabled(False)
        self.update_status_badge("Testing...")
        self.on_test(self.provider_name, real_key, self.slot, disp_name, enabled, self)


class ProviderCard(QFrame):
    def __init__(self, provider_data: dict, db_manager, test_callback, remove_callback, models_callback, parent=None):
        super().__init__(parent)
        self.provider_data = provider_data
        self.db = db_manager
        self.test_callback = test_callback
        self.remove_callback = remove_callback
        self.models_callback = models_callback

        self.setStyleSheet("""
            ProviderCard {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Header Bar
        head = QHBoxLayout()
        head.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet("background-color: #0c0e14; border: 1px solid #1e293b; border-radius: 8px;")
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        i_lbl = QLabel()
        i_lbl.setPixmap(get_svg_pixmap("auto_fix_high" if provider_data["name"] == "Gemini" else "speed", "#2196f3", 18))
        i_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        i_lbl.setStyleSheet("background: transparent; border: none;")
        ib_lay.addWidget(i_lbl)
        head.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        p_row = QHBoxLayout()
        p_row.setSpacing(8)

        p_name = QLabel(provider_data["name"])
        p_name.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        p_row.addWidget(p_name)

        tier_pill = QLabel("Active Router Tier")
        tier_pill.setStyleSheet("""
            color: #99cbff;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background-color: rgba(33, 150, 243, 0.15);
            border: 1px solid rgba(33, 150, 243, 0.3);
            border-radius: 4px;
            padding: 1px 6px;
        """)
        p_row.addWidget(tier_pill)
        p_row.addStretch()
        title_box.addLayout(p_row)

        desc = self.get_provider_description(provider_data["name"])
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        title_box.addWidget(desc_lbl)
        head.addLayout(title_box)

        head.addStretch()

        # Count active keys
        active_count = sum(1 for k in provider_data.get("keys", {}).values() if k.get("status") and "Connected" in k.get("status"))
        active_badge = QLabel(f"{active_count} of 2 Keys Active")
        active_badge.setStyleSheet("""
            color: #4edea3;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            background-color: rgba(78, 222, 163, 0.1);
            border: 1px solid rgba(78, 222, 163, 0.3);
            border-radius: 12px;
            padding: 4px 10px;
        """)
        head.addWidget(active_badge)

        layout.addLayout(head)

        # Slots
        self.slots = {}
        for slot in [1, 2]:
            slot_data = provider_data["keys"].get(slot, {})
            slot_widget = SlotWidget(
                provider_data["name"],
                slot,
                slot_data,
                self.test_callback,
                self.remove_callback,
                self.manage_models
            )
            # Update models label if key exists
            key_id = slot_data.get("id")
            if key_id:
                models = self.models_callback(key_id)
                if models:
                    names = ", ".join([m["name"] for m in models[:4]])
                    extra = f" +{len(models) - 4} more" if len(models) > 4 else ""
                    slot_widget.models_lbl.setText(f"Models ({len(models)}): {names}{extra}")

            self.slots[slot] = slot_widget
            layout.addWidget(slot_widget)

    def manage_models(self, key_id: int, slot: int):
        from app.ui.components.model_dialog import ModelManagementDialog
        dlg = ModelManagementDialog(self.provider_data["name"], key_id, self.db, self)
        dlg.exec()

    def get_provider_description(self, name: str) -> str:
        if name == "Gemini":
            return "Primary model for large context reasoning & multi-modal comprehension"
        elif name == "Groq":
            return "Ultra-fast low-latency Llama-3 & Mixtral inference engine"
        elif name == "Mistral":
            return "High precision European reasoning and code-specialized models"
        elif name == "Cerebras":
            return "Wafer-scale instantaneous LLM token generation engine"
        return "Configured AI inference provider"


class AIProvidersPage(QWidget):
    status_updated = Signal(str)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProviderRepository(self.db)

        self.cards = {}
        self.active_threads = set()
        self._startup_tested = False

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0b0f17; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0b0f17;")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(32, 28, 32, 40)
        self.layout.setSpacing(24)

        # 1. Top Action & Command Bar
        top_bar = self.create_top_bar()
        self.layout.addLayout(top_bar)

        # 2. Telemetry Usage Stats Panel
        self.telemetry_panel = self.create_telemetry_panel()
        self.layout.addWidget(self.telemetry_panel)

        # 3. Provider Cards Layout
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(18)
        self.layout.addLayout(self.cards_layout)

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

        self.load_providers()
        setup_page_animation(self)

    def create_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        top_title = QHBoxLayout()
        top_title.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("hub", "#2196f3", 22))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        top_title.addWidget(icon_lbl)

        title = QLabel("AI Providers & API Keys")
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        top_title.addWidget(title)

        routing_pill = QLabel("Multi-Agent Routing v4.2")
        routing_pill.setStyleSheet("""
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background-color: #131b2a;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 2px 8px;
        """)
        top_title.addWidget(routing_pill)
        top_title.addStretch()
        title_box.addLayout(top_title)

        sub_lbl = QLabel("Configure API credentials, secondary failover channels, and monitor runtime token usage across model instances.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        title_box.addWidget(sub_lbl)
        bar.addLayout(title_box)

        bar.addStretch()

        # Action Buttons
        test_all_btn = QPushButton(" Test All Connections")
        test_all_btn.setIcon(get_svg_icon("sync", "#94a3b8", 14))
        test_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        test_all_btn.clicked.connect(self.verify_all_keys)
        bar.addWidget(test_all_btn)

        detailed_btn = QPushButton(" Detailed Model Statistics")
        detailed_btn.setIcon(get_svg_icon("analytics", "#ffffff", 14))
        detailed_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        detailed_btn.clicked.connect(self.show_detailed_stats)
        bar.addWidget(detailed_btn)

        return bar

    def create_telemetry_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0e131f;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header
        head = QHBoxLayout()
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 4px;")
        head.addWidget(dot)

        h_lbl = QLabel("AI API Usage Statistics")
        h_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        head.addWidget(h_lbl)

        telemetry_pill = QLabel("Telemetry: Streaming")
        telemetry_pill.setStyleSheet("""
            color: #4edea3;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background-color: rgba(78, 222, 163, 0.1);
            border: 1px solid rgba(78, 222, 163, 0.3);
            border-radius: 4px;
            padding: 1px 6px;
        """)
        head.addWidget(telemetry_pill)
        head.addStretch()

        win_lbl = QLabel("Window: Rolling 24h")
        win_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        head.addWidget(win_lbl)
        layout.addLayout(head)

        # 5 Metrics Grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(12)

        self.stat_cards = {}
        metrics_def = [
            ("total_requests", "Total Requests", "swap_horiz", "0", "+12.4% vs last week"),
            ("throughput", "Throughput (RPM)", "speed", "0 req/min", "Peak: 45 req/min"),
            ("daily_total", "Daily Total", "dashboard", "0", "Local cache active"),
            ("prompt_tokens", "Prompt Tokens", "arrow_forward", "0", "Avg 308 tok/req"),
            ("comp_tokens", "Completion Tokens", "arrow_back", "0", "Avg 92 tok/req")
        ]

        for idx, (key, title, icon, val, sub) in enumerate(metrics_def):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame:hover {
                    border-color: rgba(33, 150, 243, 0.4);
                }
            """)
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(12, 10, 12, 10)
            c_lay.setSpacing(6)

            c_head = QHBoxLayout()
            c_title = QLabel(title)
            c_title.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
            c_head.addWidget(c_title)
            c_head.addStretch()

            c_icon = QLabel()
            c_icon.setPixmap(get_svg_pixmap(icon, "#64748b", 16))
            c_icon.setStyleSheet("background: transparent; border: none;")
            c_head.addWidget(c_icon)
            c_lay.addLayout(c_head)

            val_lbl = QLabel(val)
            val_lbl.setStyleSheet("color: #f1f5f9; font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; background: transparent; border: none;")
            c_lay.addWidget(val_lbl)

            sub_lbl = QLabel(sub)
            sub_lbl.setStyleSheet("color: #4edea3 if 'vs' in sub else #64748b; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
            c_lay.addWidget(sub_lbl)

            self.stat_cards[key] = (val_lbl, sub_lbl)
            self.stats_grid.addWidget(card, 0, idx)

        layout.addLayout(self.stats_grid)
        return panel

    def load_providers(self):
        # Clear cards
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Update stats
        stats = self.repo.get_provider_usage_stats()
        total_req = sum(s.get("total_requests", 0) for s in stats)
        total_prompt = sum(s.get("total_prompt", 0) for s in stats)
        total_comp = sum(s.get("total_comp", 0) for s in stats)
        rpm = sum(s.get("req_last_min", 0) for s in stats)
        daily = sum(s.get("req_last_day", 0) for s in stats)

        self.stat_cards["total_requests"][0].setText(format_number(total_req))
        self.stat_cards["throughput"][0].setText(f"{rpm} req/min")
        self.stat_cards["daily_total"][0].setText(format_number(daily))
        self.stat_cards["prompt_tokens"][0].setText(format_number(total_prompt))
        self.stat_cards["comp_tokens"][0].setText(format_number(total_comp))

        # Render Providers
        providers = self.repo.get_providers()
        for p in providers:
            card = ProviderCard(p, self.db, self.run_test, self.remove_key, self.repo.get_models)
            self.cards[p["name"]] = card
            self.cards_layout.addWidget(card)

        if not self._startup_tested:
            self._startup_tested = True
            self.verify_all_keys()

    def verify_all_keys(self):
        providers = self.repo.get_providers()
        for p in providers:
            for slot, data in p.get("keys", {}).items():
                api_key = data.get("api_key")
                if api_key and api_key != "••••••••":
                    self.run_test(
                        p["name"],
                        api_key,
                        slot,
                        data.get("display_name"),
                        data.get("enabled", 1),
                        self.cards.get(p["name"]),
                        silent=True
                    )

    def run_test(self, provider_name: str, api_key: str, slot: int, disp_name: str, enabled: int, card_widget, silent: bool = False):
        worker = ProviderTestWorker(provider_name, api_key, slot, self.db)
        self.active_threads.add(worker)
        worker.finished_signal.connect(
            lambda name, slt, succ, msg, models: self.on_test_finished(
                name, api_key, slt, disp_name, enabled, succ, msg, models, worker, silent
            )
        )
        worker.start()

    def on_test_finished(self, provider_name, api_key, slot, disp_name, enabled, success, status_msg, models, worker, silent=False):
        if worker in self.active_threads:
            self.active_threads.remove(worker)
            worker.deleteLater()

        card = self.cards.get(provider_name)
        if card and slot in card.slots:
            slot_widget = card.slots[slot]
            slot_widget.test_btn.setEnabled(True)
            slot_widget.update_status_badge(status_msg)

            self.status_updated.emit(f"AI Status: {provider_name} - {status_msg}")

            if success:
                self.repo.save_api_key(provider_name, api_key, status_msg, slot, disp_name, enabled)

                keys = self.repo.get_providers()
                p_keys = next((p["keys"] for p in keys if p["name"] == provider_name), {})
                key_id = p_keys.get(slot, {}).get("id")

                if key_id and models:
                    self.repo.save_models(provider_name, key_id, models)

                if not silent:
                    QMessageBox.information(self, "Success", f"Successfully authenticated with {provider_name}.")
            else:
                if not silent:
                    QMessageBox.warning(self, "Validation Failed", f"Failed to authenticate with {provider_name}.\nError: {status_msg}")

            self.load_providers()

    def show_detailed_stats(self):
        from app.ui.components.usage_dialog import UsageStatisticsDialog
        dlg = UsageStatisticsDialog(self.db, self)
        dlg.exec()

    def remove_key(self, provider_name, slot, key_id):
        reply = QMessageBox.question(self, "Remove Key", "Are you sure you want to remove this key?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_api_key(key_id)
            self.load_providers()
