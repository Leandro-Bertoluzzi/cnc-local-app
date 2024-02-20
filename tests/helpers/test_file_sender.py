from helpers.fileSender import FileSender
import pytest
import threading


class TestFileSender:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        # Mock GRBL controller object
        self.grbl_controller = mocker.MagicMock()

        # Create an instance of Terminal
        self.file_sender = FileSender(self.grbl_controller)

    def test_file_set_file_path(self):
        # Call method under test
        self.file_sender.set_file('/path/to/file.nc')

        # Assertions
        assert self.file_sender.file_path == '/path/to/file.nc'

    @pytest.mark.parametrize("file_path", ['', '/path/to/file.gcode'])
    @pytest.mark.parametrize("running", [False, True])
    def test_file_sender_start(self, mocker, file_path, running):
        # Mock attributes
        self.file_sender.file_path = file_path
        self.file_sender.running = running

        # Mock thread
        mock_thread_create = mocker.patch.object(threading.Thread, '__init__', return_value=None)
        mock_thread_start = mocker.patch.object(threading.Thread, 'start')

        # Call method under test
        self.file_sender.start()

        # Assertions
        assert mock_thread_create.call_count == (1 if file_path and not running else 0)
        assert mock_thread_start.call_count == (1 if file_path and not running else 0)
        assert self.file_sender.running is (False if not file_path and not running else True)

    @pytest.mark.parametrize("running", [False, True])
    def test_file_sender_pause(self, mocker, running):
        # Set attributes for test
        self.file_sender.running = running

        # Mock GRBL methods
        mock_grbl_pause = mocker.patch.object(
            self.file_sender.grbl_controller,
            'setPaused'
        )

        # Call method under test
        self.file_sender.pause()

        # Assertions
        assert self.file_sender.paused == running
        assert mock_grbl_pause.call_count == (1 if running else 0)
        if running:
            mock_grbl_pause.assert_called_with(True)

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_resume(self, mocker, running, paused):
        # Set attributes for test
        self.file_sender.running = running
        self.file_sender.paused = paused

        # Mock GRBL methods
        mock_grbl_pause = mocker.patch.object(
            self.file_sender.grbl_controller,
            'setPaused'
        )

        # Call method under test
        self.file_sender.resume()

        # Assertions
        assert self.file_sender.paused == (True if paused and not running else False)
        assert mock_grbl_pause.call_count == (1 if running else 0)
        if running:
            mock_grbl_pause.assert_called_with(False)

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_toggle_paused(self, mocker, running, paused):
        # Set attributes for test
        self.file_sender.running = running
        self.file_sender.paused = paused

        # Mock GRBL methods
        mock_grbl_pause = mocker.patch.object(
            self.file_sender.grbl_controller,
            'setPaused'
        )

        # Call method under test
        self.file_sender.toggle_paused()

        # Assertions
        # final_p = not(p) r + p not(r) = p xor r
        assert self.file_sender.paused == (True if paused ^ running else False)
        assert mock_grbl_pause.call_count == (1 if running else 0)
        if running:
            mock_grbl_pause.assert_called_with(not paused)

    def test_file_sender_stop(self):
        # Call method under test
        self.file_sender.stop()

        # Assertions
        assert self.file_sender.file_thread is None
        assert self.file_sender.running is False

    def test_file_sender_send_whole_file(self, mocker):
        # Mock attributes
        self.file_sender.file_thread = threading.Thread()
        self.file_sender.file_path = 'path/to/file'

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.grbl_controller,
            'getBufferFill',
            return_value=10.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender.send_commands()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 4
        assert mock_grbl_send_command.call_count == 3
        assert self.file_sender.file_thread is None

    def test_file_sender_avoids_filling_buffer(self, mocker):
        # Mock attributes
        self.file_sender.file_thread = threading.Thread()
        self.file_sender.file_path = 'path/to/file'

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.grbl_controller,
            'getBufferFill',
            side_effect=[20.0, 20.0, 100.0, 100.0, 20.0, 20.0]
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender.send_commands()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 6
        assert mock_grbl_send_command.call_count == 3
        assert self.file_sender.file_thread is None

    def test_file_sender_thread_stopped(self, mocker):
        # Mock attributes
        self.file_sender.file_thread = threading.Thread()
        self.file_sender.file_path = 'path/to/file'

        # Mock thread life cycle
        self.count = 0

        def manage_thread(ignore: str):
            self.count = self.count + 1
            if self.count == 2:
                self.file_sender.file_thread = None

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.grbl_controller,
            'getBufferFill',
            return_value=10.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand',
            side_effect=manage_thread
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender.send_commands()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 2
        assert mock_grbl_send_command.call_count == 2
        assert self.file_sender.file_thread is None
