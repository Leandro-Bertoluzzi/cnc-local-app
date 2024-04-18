from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QGridLayout, QSizePolicy, QSpacerItem, QToolBar, QToolButton
from components.buttons.MenuButton import MenuButton
from components.CameraViewer import CameraViewer
from components.ControllerStatus import ControllerStatus
from components.TaskProgress import TaskProgress
from components.text.LogsViewer import LogsViewer
from core.grbl.types import Status, ParserState
from helpers.cncWorkerMonitor import CncWorkerMonitor
from typing import TYPE_CHECKING
from views.BaseView import BaseView

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class MonitorView(BaseView):
    def __init__(self, parent: 'MainWindow'):
        super(MonitorView, self).__init__(parent)

        # STATE MANAGEMENT
        self.device_busy = CncWorkerMonitor.is_worker_running()

        # UI
        self.setup_ui()

        # GRBL/WORKER SYNC
        self.connect_worker()

        # Start monitors
        self.logs_viewer.start_watching()

    # SETUP METHODS

    def setup_ui(self):
        """Setup UI
        """
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.status_monitor = ControllerStatus(parent=self)
        self.task_progress = TaskProgress(parent=self)
        self.logs_viewer = LogsViewer(parent=self)
        self.camera_viewer = CameraViewer(parent=self)

        ############################################
        # 0                  |                     #
        # 1      STATUS      |                     #
        #   ---------------- |                     #
        # 2     PROGRESS     |        LOGS         #
        #   ---------------- |                     #
        # 3      CAMERA      |                     #
        #   -------------------------------------- #
        # 4               BTN_BACK                 #
        ############################################

        self.createToolBars()
        layout.addWidget(self.status_monitor, 0, 0, 1, 1, Qt.AlignTop)
        layout.addWidget(self.task_progress, 1, 0, 1, 1)
        if not self.device_busy:
            self.status_monitor.setEnabled(False)
            self.task_progress.setEnabled(False)
        layout.addWidget(self.logs_viewer, 0, 1, 4, 1)
        layout.addWidget(self.camera_viewer, 2, 0)
        self.camera_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # In case the camera view is not shown
        self.camera_placeholder = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        layout.addWidget(
            MenuButton('Volver al menú', onClick=self.backToMenu),
            5, 0, 1, 2,
            alignment=Qt.AlignCenter
        )

    def connect_worker(self):
        """Synchronizes the status monitor with the CNC worker.
        """
        if self.device_busy:
            self.getWindow().worker_monitor.task_new_status.connect(self.update_task_status)

    def createToolBars(self):
        """Adds the tool bars to the Main window
        """
        self.tool_bar = QToolBar()
        self.tool_bar.setMovable(False)
        self.getWindow().addToolBar(Qt.TopToolBarArea, self.tool_bar)

        options = [
            ('Ver logs', lambda: None),
            ('Exportar', lambda: None),
            ('Pausar', self.pause_logs),
        ]

        for (label, action) in options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            self.tool_bar.addWidget(tool_button)

        self.camera_button = QToolButton()
        self.camera_button.setText('Cámara')
        self.camera_button.clicked.connect(self.toggle_camera)
        self.camera_button.setCheckable(True)
        self.camera_button.setChecked(True)
        self.tool_bar.addWidget(self.camera_button)

    # EVENTS

    def backToMenu(self):
        self.getWindow().removeToolBar(self.tool_bar)
        self.logs_viewer.stop()
        self.getWindow().backToMenu()

    def closeEvent(self, event: QCloseEvent):
        self.logs_viewer.stop()
        return super().closeEvent(event)

    # UI METHODS

    def update_task_status(
        self,
        sent_lines: int,
        processed_lines: int,
        total_lines: int,
        controller_status: Status,
        grbl_parserstate: ParserState
    ):
        self.task_progress.set_total(total_lines)
        self.task_progress.set_progress(sent_lines, processed_lines)

        self.update_device_status(
            controller_status,
            grbl_parserstate['feedrate'],
            grbl_parserstate['spindle'],
            grbl_parserstate['tool']
        )

    def update_device_status(
            self,
            status: Status,
            feedrate: float,
            spindle: float,
            tool_index: int
    ):
        self.status_monitor.set_status(status)
        self.status_monitor.set_feedrate(feedrate)
        self.status_monitor.set_spindle(spindle)
        self.status_monitor.set_tool(tool_index)

    def pause_logs(self):
        self.logs_viewer.toggle_paused()

    def toggle_camera(self):
        is_connected = self.camera_viewer.isVisible()

        if is_connected:
            self.camera_viewer.disconnect()
            self.camera_viewer.setVisible(False)
            self.layout().addItem(self.camera_placeholder, 2, 0)
            return
        self.camera_viewer.connect()
        self.camera_viewer.setVisible(True)
        self.layout().removeItem(self.camera_placeholder)