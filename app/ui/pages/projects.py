from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QCursor

from database.repository import ProjectRepository
from app.ui.pages.project_detail import ProjectDetailWidget
from app.ui.pages.project_form import ProjectFormWidget
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from app.core.palette import ColorPalette, get_current_palette
from app.core.theme import theme_manager


class SearchInputWidget(QFrame):
    """Modern search input with embedded search icon and clear button."""
    textChanged = Signal(str)

    def __init__(self, placeholder="Search projects...", parent=None):
        super().__init__(parent)
        self.setObjectName("searchContainer")
        self.setFixedHeight(36)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self.setStyleSheet("""
            #searchContainer {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            #searchContainer:focus-within {
                border: 1px solid #276125;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(8)

        # Search icon
        search_icon = QLabel()
        search_icon.setStyleSheet("background: transparent;")
        search_icon.setPixmap(get_svg_pixmap("search", "#8B9485", 16))
        layout.addWidget(search_icon)

        # Text input
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #FBF6F0;
                font-size: 13px;
                padding: 0;
            }
            QLineEdit::placeholder {
                color: #8B9485;
            }
        """)
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)

        # Clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(get_svg_icon("close", "#8B9485", 14))
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #134741;
            }
        """)
        self.clear_btn.clicked.connect(self.clear)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

    def _on_text_changed(self, text):
        self.clear_btn.setVisible(bool(text))
        self.textChanged.emit(text)

    def text(self):
        return self.line_edit.text()

    def clear(self):
        self.line_edit.clear()


class ProjectCard(QFrame):
    """Sleek project card strictly matching the Stitch project-list design."""
    def __init__(self, project_data, open_callback):
        super().__init__()
        self.project_data = project_data
        self.open_callback = open_callback

        self.setObjectName("projectCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Top Section: Title & Status Badge on left, Timestamp on right
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)

        # Left header block
        left_header = QHBoxLayout()
        left_header.setSpacing(10)

        # Project Name
        self.title_lbl = QLabel(project_data.get("name") or "Untitled Project")
        left_header.addWidget(self.title_lbl)

        # Status badge
        status = (project_data.get("status") or "Planning").strip()
        self.status_lbl = QLabel(f'<span style="font-size: 11px;">●</span>  Status: {status}')
        self.status_lbl.setProperty("status_text", status.lower())
        left_header.addWidget(self.status_lbl)
        top_row.addLayout(left_header)
        top_row.addStretch()

        # Timestamp on right
        updated_at = project_data.get("updated_at") or project_data.get("created_at") or "Recently"
        self.time_lbl = QLabel(f"Updated: {updated_at}")
        top_row.addWidget(self.time_lbl)
        layout.addLayout(top_row)

        # Description
        desc_text = (project_data.get("description") or "No description provided.").strip()
        if len(desc_text) > 160:
            desc_text = desc_text[:157] + "..."
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMinimumWidth(1)
        layout.addWidget(self.desc_lbl)

        # Divider line
        self.divider = QFrame()
        self.divider.setFixedHeight(1)
        layout.addWidget(self.divider)

        # Bottom Section: Tech Stack tags on left, Open button on right
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 2, 0, 0)
        bottom_row.setSpacing(10)

        # Stack label
        self.stack_lbl = QLabel("Stack:")
        bottom_row.addWidget(self.stack_lbl)

        # Parse tech stack items
        raw_stack = project_data.get("technology_stack") or ""
        if "," in raw_stack:
            techs = [t.strip() for t in raw_stack.split(",") if t.strip()]
        elif raw_stack.strip():
            techs = [t.strip() for t in raw_stack.split() if t.strip()]
        else:
            techs = []

        self.tech_tags = []
        if techs:
            for tech in techs[:6]:
                tag = QLabel(tech)
                self.tech_tags.append(tag)
                bottom_row.addWidget(tag)
        else:
            na_tag = QLabel("N/A")
            self.tech_tags.append(na_tag)
            bottom_row.addWidget(na_tag)

        bottom_row.addStretch()

        # Open button
        self.open_btn = QPushButton("[ Open ]  →")
        self.open_btn.setFixedHeight(32)
        self.open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_btn.clicked.connect(lambda: self.open_callback(self.project_data["id"]))
        bottom_row.addWidget(self.open_btn)

        layout.addLayout(bottom_row)

        # Theme Initialization
        from app.core.theme import get_current_palette, theme_manager
        self.palette = get_current_palette()
        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal):
        self.palette = pal
        self.setStyleSheet(f"""
            #projectCard {{
                background-color: {pal.bg_card};
                border: 1px solid {pal.border_card};
                border-radius: 8px;
            }}
            #projectCard:hover {{
                background-color: {pal.bg_surface_hover};
                border: 1px solid {pal.border_focus};
            }}
            #projectCard QLabel {{
                background: transparent;
                background-color: transparent;
            }}
        """)

        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {pal.fg_primary}; letter-spacing: -0.2px;")
        
        status_lower = self.status_lbl.property("status_text")
        if "progress" in status_lower:
            badge_style = f"background-color: {pal.accent_bg}; border: 1px solid {pal.accent}; color: {pal.accent_fg};"
        elif "active" in status_lower:
            badge_style = f"background-color: {pal.success_bg}; border: 1px solid {pal.success_border}; color: {pal.success};"
        elif "completed" in status_lower or "done" in status_lower:
            badge_style = f"background-color: {pal.bg_badge}; border: 1px solid {pal.border_subtle}; color: {pal.fg_muted};"
        else:
            badge_style = f"background-color: {pal.bg_input}; border: 1px solid {pal.border_card}; color: {pal.fg_secondary};"
        
        self.status_lbl.setStyleSheet(f"""
            {badge_style}
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)

        self.time_lbl.setStyleSheet(f"font-size: 12px; color: {pal.fg_dim}; font-weight: 400;")
        self.desc_lbl.setStyleSheet(f"font-size: 13px; color: {pal.fg_muted}; line-height: 1.4;")
        self.divider.setStyleSheet(f"background-color: {pal.border_card}; border: none;")
        self.stack_lbl.setStyleSheet(f"font-size: 12px; color: {pal.fg_dim}; font-weight: 500;")
        
        for tag in self.tech_tags:
            tag.setStyleSheet(f"""
                background-color: {pal.bg_badge};
                border: 1px solid {pal.border_subtle};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                color: {pal.fg_secondary};
            """)

        self.open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {pal.bg_surface};
                border: 1px solid {pal.border_subtle};
                border-radius: 6px;
                color: {pal.fg_primary};
                font-size: 12px;
                font-weight: 500;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background-color: {pal.bg_surface_hover};
                border: 1px solid {pal.accent};
                color: {pal.accent_fg};
            }}
            QPushButton:pressed {{
                background-color: {pal.bg_card_inner};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_callback(self.project_data["id"])
        super().mousePressEvent(event)


class ProjectEmptyState(QWidget):
    def __init__(self, action_callback, is_filtered=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 80, 40, 80)
        
        palette = get_current_palette()
        
        icon = QLabel()
        icon_name = "search" if is_filtered else "dashboard"
        icon.setPixmap(get_svg_pixmap(icon_name, palette.fg_muted, 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("No projects found" if is_filtered else "No projects yet")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {palette.fg_primary}; margin-top: 16px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel(
            "Try adjusting your search criteria." if is_filtered 
            else "Get started by creating your first project workspace."
        )
        desc.setStyleSheet(f"font-size: 13px; color: {palette.fg_muted}; margin-top: 8px; margin-bottom: 24px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        btn = QPushButton(" Clear Search" if is_filtered else " Create Project")
        btn.setIcon(get_svg_icon("refresh" if is_filtered else "plus", palette.bg_app, 14))
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {palette.accent};
                color: {palette.bg_app};
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {palette.accent_hover};
            }}
        """)
        btn.clicked.connect(action_callback)
        
        btn_container = QHBoxLayout()
        btn_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_container.addWidget(btn)
        layout.addLayout(btn_container)

class ProjectListWidget(QWidget):
    def __init__(self, db_manager, open_project_callback):
        super().__init__()
        self.db = db_manager
        self.repo = ProjectRepository(self.db)
        self.open_project_callback = open_project_callback
        self.create_project_callback = None

        self.setStyleSheet("""
            QWidget {
                background-color: #0D3A35;
            }
            QLabel {
                background: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # Top Action Bar
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(0, 0, 0, 0)
        action_bar.setSpacing(16)

        # Title + Badge + Subtitle
        header_left = QVBoxLayout()
        header_left.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title_lbl = QLabel("Projects")
        title_lbl.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #FBF6F0;
            letter-spacing: -0.3px;
        """)
        title_row.addWidget(title_lbl)

        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet("""
            background-color: #134741;
            border: 1px solid #1B5C54;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            color: #B1B7AB;
        """)
        title_row.addWidget(self.count_badge)
        title_row.addStretch()
        header_left.addLayout(title_row)

        self.subtitle_lbl = QLabel("Showing managed repositories & local workspaces")
        self.subtitle_lbl.setStyleSheet("font-size: 13px; color: #B1B7AB;")
        header_left.addWidget(self.subtitle_lbl)

        action_bar.addLayout(header_left)
        action_bar.addStretch()

        # Search Bar
        self.search_widget = SearchInputWidget("Search projects...")
        self.search_widget.textChanged.connect(self.load_projects)
        action_bar.addWidget(self.search_widget)

        # "+ New Project" Button
        self.new_btn = QPushButton()
        self.new_btn.setIcon(get_svg_icon("plus", "#ffffff", 16))
        self.new_btn.setText("  + New Project")
        self.new_btn.setFixedHeight(36)
        self.new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #276125;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self.new_btn.clicked.connect(self.create_project)
        action_bar.addWidget(self.new_btn)

        main_layout.addLayout(action_bar)

        # Subtle divider under action bar
        header_sep = QFrame()
        header_sep.setFixedHeight(1)
        header_sep.setStyleSheet("background-color: #1B5C54; border: none;")
        main_layout.addWidget(header_sep)

        # Scroll Area for Project Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0D3A35;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1B5C54;
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 4, 0, 16)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll)

        self.load_projects()

    def load_projects(self):
        query = self.search_widget.text().strip()

        # Clear existing card widgets
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        all_projects = self.repo.get_projects()
        total_count = len(all_projects)
        
        filtered_projects = self.repo.get_projects(query) if query else all_projects
        visible_count = len(filtered_projects)

        # Update badge and subtitle
        self.count_badge.setText(str(visible_count))
        if query:
            self.subtitle_lbl.setText(f"Showing {visible_count} matching projects (filtered from {total_count})")
        else:
            self.subtitle_lbl.setText(f"Showing {visible_count} managed repositories & local workspaces")

        if not filtered_projects:
            empty_action = self.search_widget.clear if query else self.create_project
            empty_state = ProjectEmptyState(empty_action, is_filtered=bool(query))
            self.cards_layout.addWidget(empty_state)
        else:
            for p in filtered_projects:
                card = ProjectCard(p, self.open_project_callback)
                self.cards_layout.addWidget(card)

    def create_project(self):
        if hasattr(self, 'create_project_callback') and self.create_project_callback:
            self.create_project_callback()

    def apply_theme_colors(self, pal: ColorPalette):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {pal.bg_app};
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        if hasattr(self, "scroll"):
            self.scroll.setStyleSheet(f"QScrollArea {{ background-color: {pal.bg_app}; border: none; }}")
        if hasattr(self, "cards_container"):
            self.cards_container.setStyleSheet(f"background-color: {pal.bg_app};")
        if hasattr(self, "cards_layout"):
            for i in range(self.cards_layout.count()):
                item = self.cards_layout.itemAt(i)
                if item and item.widget() and hasattr(item.widget(), "apply_theme_colors"):
                    item.widget().apply_theme_colors(pal)


class ProjectsPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.list_widget = ProjectListWidget(self.db_manager, self.open_project)
        self.list_widget.create_project_callback = self.show_form

        self.detail_widget = ProjectDetailWidget(self.db_manager)
        self.form_widget = ProjectFormWidget(self.db_manager)

        self.stacked_widget.addWidget(self.list_widget)   # Index 0
        self.stacked_widget.addWidget(self.detail_widget) # Index 1
        self.stacked_widget.addWidget(self.form_widget)   # Index 2

        self.detail_widget.back_requested.connect(self.show_list)
        self.form_widget.cancelled.connect(self.show_list)
        self.form_widget.saved.connect(self.open_project)

        self.apply_theme_colors(get_current_palette())

    def apply_theme_colors(self, pal: ColorPalette):
        self.setStyleSheet(f"background-color: {pal.bg_app};")
        if hasattr(self, "list_widget") and hasattr(self.list_widget, "apply_theme_colors"):
            self.list_widget.apply_theme_colors(pal)
        if hasattr(self, "detail_widget") and hasattr(self.detail_widget, "apply_theme_colors"):
            self.detail_widget.apply_theme_colors(pal)
        if hasattr(self, "form_widget") and hasattr(self.form_widget, "apply_theme_colors"):
            self.form_widget.apply_theme_colors(pal)

        # Entrance motion opacity effect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(240)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self.play_entrance_animation()

    def play_entrance_animation(self):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.3)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def open_project(self, project_id):
        self.detail_widget.load_project(project_id)
        self.stacked_widget.setCurrentIndex(1)
        self.play_entrance_animation()

    def show_form(self):
        self.stacked_widget.setCurrentIndex(2)
        self.play_entrance_animation()

    def show_list(self):
        self.list_widget.load_projects()
        self.stacked_widget.setCurrentIndex(0)
        self.play_entrance_animation()

    def minimumSizeHint(self):
        return QSize(350, 250)

