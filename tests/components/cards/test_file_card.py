import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from core.database.models import File, User
from views.FilesView import FilesView


class TestFileCard:
    file = File(user_id=1, file_name='example_file.gcode', file_path='path/example_file.gcode')

    user_test = User(
        name='test_user',
        email='test@email.com',
        password='password',
        role='admin'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(FilesView, 'refreshLayout')

        self.parent = FilesView()
        self.file.id = 1
        self.file.user = self.user_test
        self.card = FileCard(self.file, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_file_card_init(self):
        description = self.card.label_description
        assert self.card.file == self.file
        assert description.text() == 'Archivo 1: example_file.gcode\nUsuario: test_user'
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_file_card_update_file(self, mocker, dialogResponse, expected_updated):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock FS and DB methods
        generated_file_name = 'path/to/updated_name_20230720-184800.gcode'
        mock_rename_file = mocker.patch(
            'components.cards.FileCard.renameFile',
            return_value=generated_file_name
        )
        mock_update_file = mocker.patch('components.cards.FileCard.update_file')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == (1 if expected_updated else 0)
        assert mock_update_file.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_file_params = {
                'id': 1,
                'user_id': 1,
                'file_name': 'updated_name.gcode',
                'file_name_saved': generated_file_name
            }
            mock_update_file.assert_called_with(*update_file_params.values())

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_file_card_remove_file(self, mocker, msgBoxResponse, expectedMethodCalls):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock FS and DB methods
        mock_delete_file = mocker.patch('components.cards.FileCard.deleteFile')
        mock_remove_file = mocker.patch('components.cards.FileCard.remove_file')

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == expectedMethodCalls
        assert mock_remove_file.call_count == expectedMethodCalls
