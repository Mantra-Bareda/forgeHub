from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor

from database.repository import ProjectRepository
from app.ui.pages.project_detail import ProjectDetailWidget
from app.ui.pages.project_form import ProjectFormWidget
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


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
                border: 1px solid #2196f3;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(8)

        # Search icon
        search_icon = QLabel()
        search_icon.setStyleSheet("background: transparent;")
        search_icon.setPixmap(get_svg_pixmap("search", "#64748b", 16))
        layout.addWidget(search_icon)

        # Text input
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 13px;
                padding: 0;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)

        # Clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(get_svg_icon("close", "#64748b", 14))
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
                background-color: #282a30;
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
        self.setStyleSheet("""
            #projectCard {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            #projectCard:hover {
                background-color: #182338;
                border: 1px solid #2196f3;
            }
            #projectCard QLabel {
                background: transparent;
                background-color: transparent;
            }
        """)

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
        self.title_lbl.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #f1f5f9;
            letter-spacing: -0.2px;
        """)
        left_header.addWidget(self.title_lbl)

        # Status badge
        status = (project_data.get("status") or "Planning").strip()
        status_lower = status.lower()

        if "progress" in status_lower:
            dot_color = "#fbbf24"
            badge_style = "background-color: rgba(120, 53, 15, 0.45); border: 1px solid rgba(245, 158, 11, 0.4); color: #fcd34d;"
        elif "active" in status_lower:
            dot_color = "#34d399"
            badge_style = "background-color: rgba(6, 78, 59, 0.45); border: 1px solid rgba(16, 185, 129, 0.4); color: #6ee7b7;"
        elif "completed" in status_lower or "done" in status_lower:
            dot_color = "#94a3b8"
            badge_style = "background-color: rgba(30, 41, 59, 0.6); border: 1px solid rgba(71, 85, 105, 0.4); color: #94a3b8;"
        else:
            dot_color = "#60a5fa"
            badge_style = "background-color: rgba(30, 58, 138, 0.45); border: 1px solid rgba(59, 130, 246, 0.4); color: #93c5fd;"

        status_lbl = QLabel(f'<span style="color: {dot_color}; font-size: 11px;">●</span>  Status: {status}')
        status_lbl.setStyleSheet(f"""
            {badge_style}
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        left_header.addWidget(status_lbl)
        top_row.addLayout(left_header)
        top_row.addStretch()

        # Timestamp on right
        updated_at = project_data.get("updated_at") or project_data.get("created_at") or "Recently"
        time_lbl = QLabel(f"Updated: {updated_at}")
        time_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 400;")
        top_row.addWidget(time_lbl)
        layout.addLayout(top_row)

        # Description
        desc_text = (project_data.get("description") or "No description provided.").strip()
        if len(desc_text) > 160:
            desc_text = desc_text[:157] + "..."
        desc_lbl = QLabel(desc_text)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 13px; color: #94a3b8; line-height: 1.4;")
        layout.addWidget(desc_lbl)

        # Divider line
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #1e293b; border: none;")
        layout.addWidget(divider)

        # Bottom Section: Tech Stack tags on left, Open button on right
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 2, 0, 0)
        bottom_row.setSpacing(10)

        # Stack label
        stack_lbl = QLabel("Stack:")
        stack_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        bottom_row.addWidget(stack_lbl)

        # Parse tech stack items
        raw_stack = project_data.get("technology_stack") or ""
        if "," in raw_stack:
            techs = [t.strip() for t in raw_stack.split(",") if t.strip()]
        elif raw_stack.strip():
            techs = [t.strip() for t in raw_stack.split() if t.strip()]
        else:
            techs = []

        if techs:
            for tech in techs[:6]:
                tag = QLabel(tech)
                tag.setStyleSheet("""
                    background-color: #191b22;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 12px;
                    color: #cbd5e1;
                """)
                bottom_row.addWidget(tag)
        else:
            na_tag = QLabel("N/A")
            na_tag.setStyleSheet("""
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                color: #64748b;
            """)
            bottom_row.addWidget(na_tag)

        bottom_row.addStretch()

        # Open button
        self.open_btn = QPushButton("[ Open ]  →")
        self.open_btn.setFixedHeight(32)
        self.open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 12px;
                font-weight: 500;
                padding: 4px 14px;
            }
            QPushButton:hover {
                background-color: #243248;
                border: 1px solid #2196f3;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #192233;
            }
        """)
        self.open_btn.clicked.connect(lambda: self.open_callback(self.project_data["id"]))
        bottom_row.addWidget(self.open_btn)

        layout.addLayout(bottom_row)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_callback(self.project_data["id"])
        super().mousePressEvent(event)


class ProjectEmptyState(QFrame):
    """Empty state displayed when no projects exist or search yields no results."""
    def __init__(self, on_action_callback, is_filtered=False):
        super().__init__()
        self.setObjectName("emptyStateFrame")
        self.setStyleSheet("""
            #emptyStateFrame {
                background-color: #101623;
                border: 1px dashed #334155;
                border-radius: 8px;
            }
            #emptyStateFrame QLabel {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 48, 32, 48)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon circle
        icon_circle = QFrame()
        icon_circle.setFixedSize(48, 48)
        icon_circle.setStyleSheet("""
            background-color: #1e293b;
            border-radius: 24px;
        """)
        icon_circle_layout = QVBoxLayout(icon_circle)
        icon_circle_layout.setContentsMargins(0, 0, 0, 0)
        icon_circle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("folder_off", "#64748b", 24))
        icon_lbl.setStyleSheet("background: transparent;")
        icon_circle_layout.addWidget(icon_lbl)
        layout.addWidget(icon_circle, 0, Qt.AlignmentFlag.AlignCenter)

        if is_filtered:
            title_text = "No projects found."
            sub_text = "No projects matched your search criteria. Try a different query or clear the filter."
            btn_text = "Reset Search"
        else:
            title_text = "No projects yet."
            sub_text = "Get started by creating your first managed project or repository workspace."
            btn_text = "+ New Project"

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)

        sub = QLabel(sub_text)
        sub.setStyleSheet("font-size: 13px; color: #94a3b8; max-width: 420px;")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub, 0, Qt.AlignmentFlag.AlignCenter)

        act_btn = QPushButton(btn_text)
        act_btn.setFixedHeight(34)
        act_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        act_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 12px;
                font-weight: 500;
                padding: 0 16px;
                margin-top: 6px;
            }
            QPushButton:hover {
                background-color: #243248;
                border: 1px solid #2196f3;
                color: #ffffff;
            }
        """)
        act_btn.clicked.connect(on_action_callback)
        layout.addWidget(act_btn, 0, Qt.AlignmentFlag.AlignCenter)


class ProjectListWidget(QWidget):
    def __init__(self, db_manager, open_project_callback):
        super().__init__()
        self.db = db_manager
        self.repo = ProjectRepository(self.db)
        self.open_project_callback = open_project_callback
        self.create_project_callback = None

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f17;
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
            color: #f1f5f9;
            letter-spacing: -0.3px;
        """)
        title_row.addWidget(title_lbl)

        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet("""
            background-color: #282a30;
            border: 1px solid #404752;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
        """)
        title_row.addWidget(self.count_badge)
        title_row.addStretch()
        header_left.addLayout(title_row)

        self.subtitle_lbl = QLabel("Showing managed repositories & local workspaces")
        self.subtitle_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
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
                background-color: #2196f3;
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
        header_sep.setStyleSheet("background-color: #1e293b; border: none;")
        main_layout.addWidget(header_sep)

        # Scroll Area for Project Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0b0f17;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1e293b;
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


class ProjectsPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.setStyleSheet("background-color: #0b0f17;")

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
        self.form_widget.saved.connect(self.show_list)

        # Entrance motion opacity effect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(280)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self.play_entrance_animation()

    def play_entrance_animation(self):
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(0.0)
        self._fade_anim.setStartValue(0.0)
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
