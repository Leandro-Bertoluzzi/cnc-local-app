import pytest
from PyQt5.QtWidgets import QDialogButtonBox

from MainWindow import MainWindow
from components.MenuButton import MenuButton
from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from views.FilesView import FilesView
from database.models.file import File

class TestFilesView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        file_1 = File(user_id=1, file_name='example-file-1', file_path='1/example-file-1')
        file_2 = File(user_id=1, file_name='example-file-2', file_path='1/example-file-2')
        file_3 = File(user_id=1, file_name='example-file-3', file_path='1/example-file-3')
        self.files_list = [file_1, file_2, file_3]

        # Patch the getAllFilesFromUser method with the mock function
        self.mock_get_all_files = mocker.patch('views.FilesView.getAllFilesFromUser', return_value=self.files_list)

        # Create an instance of FilesView
        self.parent = MainWindow()
        self.files_view = FilesView(parent=self.parent)
        qtbot.addWidget(self.files_view)

    def test_files_view_init(self, qtbot):
        # Validate DB calls
        self.mock_get_all_files.assert_called_once()

        # Validate amount of each type of widget
        assert self.count_widgets_with_type(MenuButton) == 2
        assert self.count_widgets_with_type(FileCard) == 3

    def test_files_view_refresh_layout(self, qtbot):
        # We remove a file
        self.files_list.pop()

        # Call the refreshLayout method
        self.files_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_files.call_count == 2

        # Validate amount of each type of widget
        assert self.count_widgets_with_type(MenuButton) == 2
        assert self.count_widgets_with_type(FileCard) == 2

    def test_files_view_create_file(self, qtbot, mocker):
        # Mock FileDataDialog methods
        mock_inputs = 'example-file-4'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_file(user_id, file_name, file_path):
            file_4 = File(user_id=1, file_name='example-file-4', file_path='1/example-file-4')
            self.files_list.append(file_4)
            return

        mock_create_file = mocker.patch('views.FilesView.createFile', side_effect=side_effect_create_file)

        # Call the createFile method
        self.files_view.createFile()

        # Validate DB calls
        assert mock_create_file.call_count == 1
        assert self.mock_get_all_files.call_count == 2

        # Validate amount of each type of widget
        assert self.count_widgets_with_type(MenuButton) == 2
        assert self.count_widgets_with_type(FileCard) == 4

    # Helper method
    def count_widgets_with_type(self, widgetType):
        count = 0
        for i in range(self.files_view.layout.count()):
            widget = self.files_view.layout.itemAt(i).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count