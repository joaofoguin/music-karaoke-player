class ThemeManager:
    """Fornece os estilos visuais da aplicação."""

    def obter_tema_qss(tema: str) -> str:
        if tema == "midnight":
            return """
            QMainWindow { background: #0b0d11; color: #f3f4f6; }
            QMenuBar { background: #131720; color: #e5e7eb; border-bottom: 1px solid #1f2937; padding: 4px 8px; }\n            QMenuBar::item { padding: 4px 8px; margin: 0; }
            QMenuBar::item:selected { background: #2563eb; color: #ffffff; padding: 4px 8px; margin: 0; }\n            QMenu::item:selected { background: #2563eb; color: #ffffff; }
            QMenu { background: #131720; color: #f3f4f6; border: 1px solid #374151; }
            QMenu::item { padding: 6px 28px 6px 12px; }
            QFrame#panel { background: #131720; border: 1px solid #1f2937; border-radius: 8px; }
            QFrame#playerBar { background: #0f131a; border: 1px solid #1f2937; border-radius: 8px; }
            QLabel#sectionTitle { color: #60a5fa; font-size: 12px; font-weight: 700; letter-spacing: 1px; padding: 4px; }
            QLabel#trackTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
            QLabel#trackMetadata { color: #9ca3af; font-size: 12px; }
            QTreeView, QScrollArea { background: #0b0d11; border: 1px solid #1f2937; color: #e5e7eb; border-radius: 4px; }
            QTreeView::item:selected { background: #2563eb; color: #ffffff; }
            QHeaderView::section { background: #131720; color: #9ca3af; border: 0; border-bottom: 1px solid #1f2937; padding: 6px; }
            QPushButton { background: #1f2937; color: #f3f4f6; border: 1px solid #374151; border-radius: 4px; min-height: 28px; padding: 2px 10px; font-weight: 500; }
            QPushButton:hover { background: #374151; border-color: #4b5563; }
            QPushButton:pressed { background: #111827; }
            QPushButton:disabled { color: #6b7280; background: #131720; border-color: #1f2937; }
            QPushButton#mediaButton { background: transparent; border: 0; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 4px; border-radius: 18px; }
            QPushButton#mediaButton:hover { background: #1f2937; }
            QPushButton#mediaButton:pressed { background: #111827; }
            QPushButton#mediaButton:checked { background: rgba(37, 99, 235, 0.3); border: 1px solid #3b82f6; }
            QPushButton#queueActionButton { background: transparent; border: 0; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; padding: 4px; border-radius: 5px; }
            QPushButton#queueActionButton:hover { background: rgba(59, 130, 246, 0.18); }
            QPushButton#queueActionButton:pressed { background: rgba(59, 130, 246, 0.28); }
            QToolButton#panelAction { background: transparent; border: 0; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 5px; border-radius: 6px; }
            QToolButton#panelAction:hover { background: rgba(59, 130, 246, 0.16); }
            QToolButton#panelAction:pressed { background: rgba(59, 130, 246, 0.24); }
            QPushButton#mainPlayButton { background: #2563eb; color: #ffffff; border: 0; border-radius: 20px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; }
            QPushButton#mainPlayButton:hover { background: #3b82f6; }
            QPushButton#mainPlayButton:pressed { background: #1d4ed8; }
            QSlider::groove:horizontal { height: 6px; background: #1f2937; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #60a5fa; border-radius: 7px; }
            QScrollBar:vertical { background: #0b0d11; width: 10px; }
            QScrollBar::handle:vertical { background: #374151; border-radius: 4px; min-height: 24px; }
            """
        elif tema == "light":
            return """
            QMainWindow { background: #f3f4f6; color: #111827; }
            QMenuBar { background: #ffffff; color: #374151; border-bottom: 1px solid #e5e7eb; padding: 4px 8px; }\n            QMenuBar::item { padding: 4px 8px; margin: 0; }
            QMenuBar::item:selected { background: #e5e7eb; padding: 4px 8px; margin: 0; }\n            QMenu::item:selected { background: #e5e7eb; }
            QMenu { background: #ffffff; color: #111827; border: 1px solid #d1d5db; }
            QMenu::item { padding: 6px 28px 6px 12px; }
            QFrame#panel { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
            QFrame#playerBar { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
            QLabel#sectionTitle { color: #2563eb; font-size: 12px; font-weight: 700; letter-spacing: 1px; padding: 4px; }
            QLabel#trackTitle { color: #111827; font-size: 16px; font-weight: 700; }
            QLabel#trackMetadata { color: #6b7280; font-size: 12px; }
            QTreeView, QScrollArea { background: #f9fafb; border: 1px solid #e5e7eb; color: #111827; border-radius: 4px; }
            QTreeView::item:selected { background: #2563eb; color: #ffffff; }
            QHeaderView::section { background: #f3f4f6; color: #4b5563; border: 0; border-bottom: 1px solid #e5e7eb; padding: 6px; }
            QPushButton { background: #f9fafb; color: #1f2937; border: 1px solid #d1d5db; border-radius: 4px; min-height: 28px; padding: 2px 10px; font-weight: 500; }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:pressed { background: #d1d5db; }
            QPushButton:disabled { color: #9ca3af; background: #f3f4f6; border-color: #e5e7eb; }
            QPushButton#mediaButton { background: transparent; border: 0; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 4px; border-radius: 18px; }
            QPushButton#mediaButton:hover { background: #e5e7eb; }
            QPushButton#mediaButton:pressed { background: #d1d5db; }
            QPushButton#mediaButton:checked { background: rgba(37, 99, 235, 0.15); border: 1px solid #2563eb; }
            QPushButton#mainPlayButton { background: #2563eb; color: #ffffff; border: 0; border-radius: 20px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; }
            QPushButton#mainPlayButton:hover { background: #1d4ed8; }
            QPushButton#mainPlayButton:pressed { background: #1e40af; }
            QSlider::groove:horizontal { height: 6px; background: #e5e7eb; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #2563eb; border-radius: 7px; }
            QScrollBar:vertical { background: #f3f4f6; width: 10px; }
            QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 4px; min-height: 24px; }
            """
        else:
            # Tema Escuro Moderno Padrão
            return """
            QMainWindow { background: #171717; color: #f4f4f4; }
            QMenuBar { background: #242424; color: #d8d8d8; border-bottom: 1px solid #3c3c3c; padding: 3px 8px; }\n            QMenuBar::item { padding: 3px 8px; margin: 0; }
            QMenuBar::item:selected { background: #3c3c3c; padding: 3px 8px; margin: 0; }\n            QMenu::item:selected { background: #3c3c3c; }
            QMenu { background: #242424; color: #f4f4f4; border: 1px solid #4a4a4a; }
            QMenu::item { padding: 6px 28px 6px 12px; }
            QFrame#panel { background: #242424; border: 1px solid #3f3f3f; border-radius: 6px; }
            QFrame#playerBar { background: #181818; border: 1px solid #303030; border-radius: 6px; }
            QLabel#sectionTitle { color: #f0f0f0; font-size: 12px; font-weight: 700; letter-spacing: 1px; padding: 4px; }
            QLabel#trackTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
            QLabel#trackMetadata { color: #a8a8a8; font-size: 12px; }
            QTreeView, QScrollArea { background: #1d1d1d; border: 1px solid #393939; color: #d8d8d8; }
            QTreeView::item:selected { background: #365d8d; color: #ffffff; }
            QHeaderView::section { background: #2c2c2c; color: #bdbdbd; border: 0; border-bottom: 1px solid #454545; padding: 5px; }
            QPushButton { background: #363636; color: #f2f2f2; border: 1px solid #4d4d4d; border-radius: 4px; min-height: 26px; padding: 2px 8px; }
            QPushButton:hover { background: #4a4a4a; }
            QPushButton:pressed { background: #2b2b2b; }
            QPushButton:disabled { color: #777777; background: #2a2a2a; }
            QPushButton#mediaButton { background: transparent; border: 0; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 4px; border-radius: 18px; }
            QPushButton#mediaButton:hover { background: rgba(255, 255, 255, 0.12); }
            QPushButton#mediaButton:pressed { background: rgba(255, 255, 255, 0.2); }
            QPushButton#mediaButton:checked { background: rgba(59, 130, 246, 0.25); border: 1px solid #3b82f6; }
            QPushButton#mainPlayButton { background: #f4f4f4; border: 0; border-radius: 20px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; }
            QPushButton#mainPlayButton:hover { background: #ffffff; }
            QPushButton#mainPlayButton:pressed { background: #e0e0e0; }
            QSlider::groove:horizontal { height: 6px; background: #4a4a4a; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #e0e0e0; border-radius: 7px; }
            QScrollBar:vertical { background: #1d1d1d; width: 10px; }
            QScrollBar::handle:vertical { background: #555555; border-radius: 4px; min-height: 24px; }
            """
