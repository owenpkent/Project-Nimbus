from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from .bridge import ControllerBridge
from .config import ControllerConfig


def qml_path() -> Path:
    # Resolve qml directory relative to this file (project-root/qml)
    here = Path(__file__).resolve().parent
    project_root = here.parent
    return project_root / "qml" / "Main.qml"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Project Nimbus - QML UI")

    # Config and bridge
    config = ControllerConfig()
    bridge = ControllerBridge(config)

    engine = QQmlApplicationEngine()
    # Expose bridge and config to QML
    engine.rootContext().setContextProperty("controller", bridge)
    engine.rootContext().setContextProperty("config", config)

    # Load QML
    main_qml = qml_path()
    engine.load(QUrl.fromLocalFile(str(main_qml)))

    if not engine.rootObjects():
        # Failed to load QML
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
