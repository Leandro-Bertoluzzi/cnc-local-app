import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton
from celery.result import AsyncResult
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from components.dialogs.TaskDataDialog import TaskDataDialog
from core.database.models import Task
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from views.TasksView import TasksView


class TestTaskCard:
    task = Task(
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name='Example task'
    )

    @pytest.fixture(scope='function')
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture):
        mocker.patch.object(TasksView, 'refreshLayout')

        # Patch the DB methods
        mocker.patch.object(FileRepository, 'get_all_files_from_user', return_value=[])
        mocker.patch.object(ToolRepository, 'get_all_tools', return_value=[])
        mocker.patch.object(MaterialRepository, 'get_all_materials', return_value=[])

        self.parent = TasksView()
        self.task.id = 1

        self.card = TaskCard(self.task, False, parent=self.parent)
        qtbot.addWidget(self.card)

    @pytest.mark.parametrize(
            "status,expected_buttons",
            [
                ('pending_approval', 2),
                ('on_hold', 2),
                ('finished', 0),
                ('rejected', 1),
                ('cancelled', 1)
            ]
        )
    def test_task_card_init(
        self,
        qtbot: QtBot,
        helpers,
        status,
        expected_buttons
    ):
        # Mock task status
        self.task.status = status
        self.task.id = 1

        # Instantiate card
        card = TaskCard(self.task, False)
        qtbot.addWidget(card)

        # Assertions
        assert card.task == self.task
        assert card.layout() is not None
        assert card.label_description.text() == f'Tarea 1: Example task\nEstado: {status}'
        assert helpers.count_widgets(card.layout_buttons, QPushButton) == expected_buttons

    @pytest.mark.parametrize(
            "status,expected_buttons",
            [
                ('pending_approval', 2),
                ('on_hold', 1),
                ('finished', 0),
                ('rejected', 1),
                ('cancelled', 1)
            ]
        )
    def test_task_card_init_device_busy(
        self,
        qtbot: QtBot,
        helpers,
        status,
        expected_buttons
    ):
        # Mock task status
        self.task.status = status
        self.task.id = 1

        # Instantiate card
        card = TaskCard(self.task, True)
        qtbot.addWidget(card)

        # Assertions
        assert card.task == self.task
        assert card.layout() is not None
        assert card.label_description.text() == f'Tarea 1: Example task\nEstado: {status}'
        assert helpers.count_widgets(card.layout_buttons, QPushButton) == expected_buttons

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_update_task(
        self,
        setup_method,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch.object(TaskRepository, 'update_task')

        # Call the updateTask method
        self.card.updateTask()

        # Validate DB calls
        assert mock_update_task.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_task_params = {
                'id': 1,
                'user_id': 1,
                'file_id': 2,
                'tool_id': 3,
                'material_id': 4,
                'name': 'Updated task',
                'note': 'Just a simple description',
                'priority': 0,
            }
            mock_update_task.assert_called_with(*update_task_params.values())

    def test_task_card_update_task_db_error(self, setup_method, mocker: MockerFixture):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch.object(
            TaskRepository,
            'update_task',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the updateTask method
        self.card.updateTask()

        # Validate DB calls
        assert mock_update_task.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_task_card_remove_task(
        self,
        setup_method,
        mocker: MockerFixture,
        msgBoxResponse,
        expectedMethodCalls
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_task = mocker.patch.object(TaskRepository, 'remove_task')

        # Call the removeTask method
        self.card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == expectedMethodCalls

    def test_task_card_remove_task_db_error(self, setup_method, mocker: MockerFixture):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_task = mocker.patch.object(
            TaskRepository,
            'remove_task',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeTask method
        self.card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "status",
            [
                'pending_approval',
                'on_hold',
                'in_progress',
                'finished',
                'rejected',
                'cancelled'
            ]
        )
    def test_task_card_show_task_progress(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        helpers,
        status
    ):
        # Mock task status
        self.task.status = status

        # Mock Celery task metadata
        task_metadata = {
            'status': 'PROGRESS',
            'result': {
                'percentage': 50,
                'progress': 10,
                'total_lines': 20
            }
        }

        # Mock Celery methods
        mock_query_task = mocker.patch.object(
            AsyncResult,
            '__init__',
            return_value=None
        )
        mock_query_task_info = mocker.patch.object(
            AsyncResult,
            '_get_task_meta',
            return_value=task_metadata
        )

        # Instantiate card
        card = TaskCard(self.task, False)
        qtbot.addWidget(card)

        # Assertions
        if status == 'in_progress':
            expected_text = 'Tarea 1: Example task\nEstado: in_progress\nProgreso: 10/20 (50%)'
            assert card.label_description.text() == expected_text
            assert mock_query_task.call_count == 1
            assert mock_query_task_info.call_count == 2
            assert helpers.count_widgets(card.layout_buttons, QPushButton) == 0
            return

        assert card.label_description.text() == f'Tarea 1: Example task\nEstado: {status}'
        assert mock_query_task.call_count == 0
        assert mock_query_task_info.call_count == 0

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_cancel_task(
        self,
        setup_method,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock TaskCancelDialog methods
        mock_input = 'A valid cancellation reason'
        mocker.patch.object(TaskCancelDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskCancelDialog, 'getInput', return_value=mock_input)

        # Mock DB method
        mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

        # Call the removeTask method
        self.card.cancelTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == expected_updated

    def test_task_card_cancel_task_db_error(self, setup_method, mocker: MockerFixture):
        # Mock TaskCancelDialog methods
        mock_input = 'A valid cancellation reason'
        mocker.patch.object(TaskCancelDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(TaskCancelDialog, 'getInput', return_value=mock_input)

        # Mock DB method
        mock_update_task_status = mocker.patch.object(
            TaskRepository,
            'update_task_status',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeTask method
        self.card.cancelTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxRun",
            [
                QMessageBox.Yes,
                QMessageBox.No
            ]
        )
    @pytest.mark.parametrize("task_in_progress", [True, False])
    def test_task_card_run_task(
        self,
        setup_method,
        mocker,
        msgBoxRun,
        task_in_progress
    ):
        # Mock DB methods
        mocker.patch.object(
            TaskRepository,
            'are_there_tasks_in_progress',
            return_value=task_in_progress
        )
        # Mock message box methods
        mocker.patch.object(
            QMessageBox,
            'exec',
            return_value=msgBoxRun
        )
        mock_info_popup = mocker.patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok)
        mock_error_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)
        # Mock task manager methods
        mock_add_task_in_queue = mocker.patch('components.cards.RequestCard.executeTask.delay')

        # Call the approveTask method
        self.card.runTask()

        # Validate call to tasks manager
        accepted_run = (msgBoxRun == QMessageBox.Yes)
        expected_run = not task_in_progress and accepted_run
        assert mock_add_task_in_queue.call_count == (1 if expected_run else 0)
        assert mock_info_popup.call_count == (1 if expected_run else 0)
        assert mock_error_popup.call_count == (1 if task_in_progress else 0)

    def test_task_card_run_task_db_error(
        self,
        setup_method,
        mocker
    ):
        # Mock DB methods
        mocker.patch.object(
            TaskRepository,
            'are_there_tasks_in_progress',
            side_effect=Exception('mocked-error')
        )
        # Mock message box methods
        mocker.patch.object(
            QMessageBox,
            'exec',
            return_value=QMessageBox.Yes
        )
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)
        # Mock task manager methods
        mock_add_task_in_queue = mocker.patch('components.cards.RequestCard.executeTask.delay')

        # Call the approveTask method
        self.card.runTask()

        # Validate call to tasks manager
        assert mock_add_task_in_queue.call_count == 0
        assert mock_popup.call_count == 1
