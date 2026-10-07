from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMessageBox, QCheckBox,
    QGridLayout, QGraphicsOpacityEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication
from database.repository import ProviderRepository
from providers import get_provider
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from app.core.palette import ColorPalette
from app.core.theme import get_current_palette, theme_manager


def setup_page_animation(widget: QWidget):
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(1.0)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(240)
    anim.setStartValue(0.3)
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
        self.palette = get_current_palette()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Top line: Enable switch, Slot Label, Status Badge
        top_line = QHBoxLayout()
        top_line.setSpacing(10)

        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(slot_data.get("enabled", 1) == 1)
        top_line.addWidget(self.enable_cb)

        slot_title = f"Slot {slot} • {'Production Primary' if slot == 1 else 'Secondary Failover'}"
        self.title_lbl = QLabel(slot_title)
        top_line.addWidget(self.title_lbl)

        route_type = "Default Routing" if slot == 1 else "Failover Target"
        self.rt_lbl = QLabel(route_type)
        top_line.addWidget(self.rt_lbl)

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
        self.n_lbl = QLabel("Custom Key Label")
        name_box.addWidget(self.n_lbl)

        self.name_input = QLineEdit()
        self.name_input.setText(slot_data.get("display_name") or f"{provider_name}-Key-{slot}")
        name_box.addWidget(self.name_input)
        inputs_row.addLayout(name_box, stretch=1)

        # Secret Key with eye toggle & copy
        key_box = QVBoxLayout()
        key_box.setSpacing(4)

        k_head = QHBoxLayout()
        self.k_lbl = QLabel("API Secret Key")
        k_head.addWidget(self.k_lbl)
        k_head.addStretch()

        last_tested = slot_data.get("last_tested") or "Never tested"
        self.tested_lbl = QLabel(f"Last tested: {last_tested[:19] if len(last_tested) > 19 else last_tested}")
        k_head.addWidget(self.tested_lbl)
        key_box.addLayout(k_head)

        self.key_frame = QFrame()
        kf_lay = QHBoxLayout(self.key_frame)
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
        kf_lay.addWidget(self.key_input)

        self.show_key_btn = QPushButton()
        self.show_key_btn.setFixedSize(22, 22)
        self.show_key_btn.setToolTip("Toggle Visibility")
        self.show_key_btn.clicked.connect(self.toggle_password_visibility)
        kf_lay.addWidget(self.show_key_btn)

        self.copy_btn = QPushButton()
        self.copy_btn.setFixedSize(22, 22)
        self.copy_btn.setToolTip("Copy API Key")
        self.copy_btn.clicked.connect(self.copy_key)
        kf_lay.addWidget(self.copy_btn)

        key_box.addWidget(self.key_frame)
        inputs_row.addLayout(key_box, stretch=2)

        self.name_input.setMinimumWidth(0)
        self.key_input.setMinimumWidth(0)
        self.key_frame.setMinimumWidth(0)

        layout.addLayout(inputs_row)

        # Models info badge on its own dedicated row to prevent horizontal expansion
        key_id = slot_data.get("id")
        self.models_lbl = QLabel()
        self.models_lbl.setWordWrap(True)
        self.models_lbl.setMinimumWidth(1)
        layout.addWidget(self.models_lbl)

        # Bottom Actions Bar
        actions_bar = QHBoxLayout()
        actions_bar.setSpacing(8)
        actions_bar.addStretch()

        self.manage_models_btn = None
        self.remove_btn = None
        if key_id:
            self.manage_models_btn = QPushButton(" Manage Models")
            self.manage_models_btn.clicked.connect(lambda: self.on_manage_models(key_id, slot))
            actions_bar.addWidget(self.manage_models_btn)

            self.remove_btn = QPushButton(" Remove")
            self.remove_btn.clicked.connect(lambda: self.on_remove(self.provider_name, slot, key_id))
            actions_bar.addWidget(self.remove_btn)

        self.test_btn = QPushButton(" Test && Save")
        self.test_btn.clicked.connect(self.trigger_test)
        actions_bar.addWidget(self.test_btn)

        layout.addLayout(actions_bar)

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            SlotWidget {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {self.palette.border_subtle};
                background-color: {self.palette.bg_input};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.palette.accent};
                border-color: {self.palette.accent};
            }}
        """)
        self.title_lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        self.rt_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 10px; background-color: {self.palette.bg_input}; border: 1px solid {self.palette.border_card}; border-radius: 4px; padding: 2px 6px;")
        
        # We need to re-call update_status_badge to refresh its colors
        self.update_status_badge(self.status_badge.text())

        self.n_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_card};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 6px 10px;
            }}
            QLineEdit:focus {{
                border-color: {self.palette.accent};
            }}
        """)
        self.k_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        self.tested_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 10px; background: transparent; border: none;")
        
        self.key_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_card};
                border-radius: 6px;
            }}
            QFrame:focus-within {{
                border-color: {self.palette.accent};
            }}
        """)
        self.key_input.setStyleSheet(f"background: transparent; border: none; color: {self.palette.fg_primary}; font-family: 'JetBrains Mono', monospace; font-size: 12px; padding: 6px 0;")
        
        self.show_key_btn.setIcon(get_svg_icon("visibility" if "visibility" in get_svg_icon.__name__ else "description", pal.fg_muted, 14))
        self.show_key_btn.setStyleSheet("background: transparent; border: none;")
        self.copy_btn.setIcon(get_svg_icon("content_copy", pal.fg_muted, 14))
        self.copy_btn.setStyleSheet("background: transparent; border: none;")
        
        self.models_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        
        if self.manage_models_btn:
            self.manage_models_btn.setIcon(get_svg_icon("tune", pal.fg_muted, 12))
            self.manage_models_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.bg_input};
                    border: 1px solid {self.palette.border_card};
                    border-radius: 6px;
                    color: {self.palette.fg_primary};
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    border-color: {self.palette.accent};
                }}
            """)
        
        if self.remove_btn:
            self.remove_btn.setIcon(get_svg_icon("delete", pal.fg_muted, 12))
            self.remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.bg_input};
                    border: 1px solid {self.palette.border_card};
                    border-radius: 6px;
                    color: {self.palette.fg_muted};
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    background-color: rgba(239, 68, 68, 0.15);
                    border-color: rgba(239, 68, 68, 0.4);
                    color: #f87171;
                }}
            """)
        
        self.test_btn.setIcon(get_svg_icon("sync", "#ffffff", 12))
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent};
            }}
            QPushButton:disabled {{
                background-color: {self.palette.border_card};
                color: {self.palette.fg_muted};
            }}
        """)

    def update_status_badge(self, text: str):
        pal = self.palette
        if "Valid" in text or "Connected" in text:
            self.status_badge.setText(" Connected & Verified")
            self.status_badge.setStyleSheet(f"""
                color: {self.palette.success};
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
            self.status_badge.setStyleSheet(f"""
                color: {self.palette.fg_muted};
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_card};
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
        self.palette = get_current_palette()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Header Bar
        head = QHBoxLayout()
        head.setSpacing(12)

        self.icon_box = QFrame()
        self.icon_box.setFixedSize(36, 36)
        ib_lay = QVBoxLayout(self.icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        self.i_lbl = QLabel()
        self.i_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.i_lbl.setStyleSheet("background: transparent; border: none;")
        ib_lay.addWidget(self.i_lbl)
        head.addWidget(self.icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        p_row = QHBoxLayout()
        p_row.setSpacing(8)

        self.p_name = QLabel(provider_data["name"])
        p_row.addWidget(self.p_name)

        self.tier_pill = QLabel("Active Router Tier")
        p_row.addWidget(self.tier_pill)
        p_row.addStretch()
        title_box.addLayout(p_row)

        desc = self.get_provider_description(provider_data["name"])
        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMinimumWidth(1)
        title_box.addWidget(self.desc_lbl)
        head.addLayout(title_box, stretch=1)

        # Count active keys
        active_count = sum(1 for k in provider_data.get("keys", {}).values() if k.get("status") and "Connected" in k.get("status"))
        self.active_badge = QLabel(f"{active_count} of 2 Keys Active")
        self.active_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        head.addWidget(self.active_badge)

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

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            ProviderCard {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 12px;
            }}
        """)
        self.icon_box.setStyleSheet(f"background-color: {self.palette.bg_app}; border: 1px solid {self.palette.border_card}; border-radius: 8px;")
        self.i_lbl.setPixmap(get_svg_pixmap("auto_fix_high" if self.provider_data["name"] == "Gemini" else "speed", pal.accent, 18))
        
        self.p_name.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        self.tier_pill.setStyleSheet(f"""
            color: #99cbff;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background-color: rgba(33, 150, 243, 0.15);
            border: 1px solid rgba(33, 150, 243, 0.3);
            border-radius: 4px;
            padding: 1px 6px;
        """)
        self.desc_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        self.active_badge.setStyleSheet(f"""
            color: {self.palette.success};
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            background-color: rgba(78, 222, 163, 0.1);
            border: 1px solid rgba(78, 222, 163, 0.3);
            border-radius: 12px;
            padding: 4px 10px;
        """)

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
        self.palette = get_current_palette()

        self.cards = {}
        self.active_threads = set()
        self._startup_tested = False

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content = QWidget()
        self.layout = QVBoxLayout(self.content)
        self.layout.setContentsMargins(18, 20, 18, 30)
        self.layout.setSpacing(18)

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

        self.scroll.setWidget(self.content)
        root_layout.addWidget(self.scroll)

        self.apply_theme_colors(self.palette)

        self.load_providers()
        setup_page_animation(self)

    def create_top_bar(self) -> QVBoxLayout:
        bar = QVBoxLayout()
        bar.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        top_row.addWidget(self.icon_lbl)

        self.title_lbl = QLabel("AI Providers & API Keys")
        top_row.addWidget(self.title_lbl)

        self.routing_pill = QLabel("Multi-Agent Routing")
        top_row.addWidget(self.routing_pill)
        top_row.addStretch()

        bar.addLayout(top_row)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(10)

        self.sub_lbl = QLabel("Configure API credentials, secondary failover channels, and monitor runtime token usage across model instances.")
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setMinimumWidth(1)
        sub_row.addWidget(self.sub_lbl, stretch=1)

        # Action Buttons
        self.test_all_btn = QPushButton(" Test All")
        self.test_all_btn.clicked.connect(self.verify_all_keys)
        sub_row.addWidget(self.test_all_btn)

        self.detailed_btn = QPushButton(" Model Statistics")
        self.detailed_btn.clicked.connect(self.show_detailed_stats)
        sub_row.addWidget(self.detailed_btn)

        bar.addLayout(sub_row)

        return bar

    def create_telemetry_panel(self) -> QFrame:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Header
        head = QHBoxLayout()
        self.dot = QFrame()
        self.dot.setFixedSize(8, 8)
        head.addWidget(self.dot)

        self.h_lbl = QLabel("AI API Usage Statistics")
        head.addWidget(self.h_lbl)

        self.telemetry_pill = QLabel("Telemetry: Streaming")
        head.addWidget(self.telemetry_pill)
        head.addStretch()

        self.win_lbl = QLabel("Window: Rolling 24h")
        head.addWidget(self.win_lbl)
        layout.addLayout(head)

        # 5 Metrics Grid (arranged across max 3 columns)
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(10)

        self.stat_cards = {}
        metrics_def = [
            ("total_requests", "Total Requests", "swap_horiz", "0", "+12.4% vs last week"),
            ("throughput", "Throughput (RPM)", "speed", "0 req/min", "Peak: 45 req/min"),
            ("daily_total", "Daily Total", "dashboard", "0", "Local cache active"),
            ("prompt_tokens", "Prompt Tokens", "arrow_forward", "0", "Avg 308 tok/req"),
            ("comp_tokens", "Completion Tokens", "arrow_back", "0", "Avg 92 tok/req")
        ]

        # To support dynamic theming of stat cards, we need references
        self.stat_card_frames = []
        self.stat_card_icons = []
        self.stat_card_titles = []
        self.stat_card_vals = []
        self.stat_card_subs = []

        for idx, (key, title, icon, val, sub) in enumerate(metrics_def):
            card = QFrame()
            card.setMinimumWidth(0)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.stat_card_frames.append(card)
            
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(10, 8, 10, 8)
            c_lay.setSpacing(4)

            c_head = QHBoxLayout()
            c_title = QLabel(title)
            c_title.setWordWrap(True)
            c_title.setMinimumWidth(1)
            self.stat_card_titles.append(c_title)
            c_head.addWidget(c_title, stretch=1)

            c_icon = QLabel()
            # Storing the icon name to dynamically set it
            c_icon.setProperty("icon_name", icon)
            self.stat_card_icons.append(c_icon)
            c_head.addWidget(c_icon)
            c_lay.addLayout(c_head)

            val_lbl = QLabel(val)
            self.stat_card_vals.append(val_lbl)
            c_lay.addWidget(val_lbl)

            sub_lbl = QLabel(sub)
            sub_lbl.setWordWrap(True)
            sub_lbl.setMinimumWidth(1)
            sub_lbl.setProperty("is_positive", 'vs' in sub)
            self.stat_card_subs.append(sub_lbl)
            c_lay.addWidget(sub_lbl)

            self.stat_cards[key] = (val_lbl, sub_lbl)
            self.stats_grid.addWidget(card, idx // 3, idx % 3)

        layout.addLayout(self.stats_grid)
        return panel

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.scroll.setStyleSheet(f"QScrollArea {{ background-color: {self.palette.bg_app}; border: none; }}")
        self.content.setStyleSheet(f"background-color: {self.palette.bg_app};")
        
        self.icon_lbl.setPixmap(get_svg_pixmap("hub", pal.accent, 22))
        self.title_lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 700; background: transparent; border: none;")
        self.routing_pill.setStyleSheet(f"""
            color: {self.palette.fg_muted};
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background-color: {self.palette.bg_card};
            border: 1px solid {self.palette.border_card};
            border-radius: 10px;
            padding: 2px 8px;
        """)
        self.sub_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        
        self.test_all_btn.setIcon(get_svg_icon("sync", pal.fg_muted, 12))
        self.test_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 500;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                border-color: {self.palette.accent};
            }}
        """)
        
        self.detailed_btn.setIcon(get_svg_icon("analytics", "#ffffff", 12))
        self.detailed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent};
            }}
        """)
        
        self.telemetry_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_app};
                border: 1px solid {self.palette.border_card};
                border-radius: 12px;
            }}
        """)
        
        self.dot.setStyleSheet(f"background-color: {self.palette.success}; border-radius: 4px;")
        self.h_lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        self.telemetry_pill.setStyleSheet(f"""
            color: {self.palette.success};
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background-color: rgba(78, 222, 163, 0.1);
            border: 1px solid rgba(78, 222, 163, 0.3);
            border-radius: 4px;
            padding: 1px 6px;
        """)
        self.win_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        
        for frame in self.stat_card_frames:
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_card};
                    border-radius: 8px;
                    padding: 10px;
                }}
                QFrame:hover {{
                    border-color: {self.palette.accent};
                }}
            """)
            
        for icon_lbl in self.stat_card_icons:
            icon_name = icon_lbl.property("icon_name")
            icon_lbl.setPixmap(get_svg_pixmap(icon_name, pal.fg_muted, 16))
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            
        for t_lbl in self.stat_card_titles:
            t_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
            
        for v_lbl in self.stat_card_vals:
            v_lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; background: transparent; border: none;")
            
        for s_lbl in self.stat_card_subs:
            is_pos = s_lbl.property("is_positive")
            color = pal.success if is_pos else pal.fg_muted
            s_lbl.setStyleSheet(f"color: {color}; font-family: 'Inter', sans-serif; font-size: 10px; background: transparent; border: none;")


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
