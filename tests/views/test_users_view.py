import pytest
from PyQt5.QtWidgets import QDialogButtonBox

from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from components.cards.UserCard import UserCard
from components.dialogs.UserDataDialog import UserDataDialog
from views.UsersView import UsersView
from core.database.models.user import User


class TestUsersView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        user_1 = User(name='John 1', email='test1@testing.com', password='1234', role='user')
        user_2 = User(name='John 2', email='test2@testing.com', password='1234', role='user')
        user_3 = User(name='John 3', email='test3@testing.com', password='1234', role='user')
        self.users_list = [user_1, user_2, user_3]

        # Patch the getAllUsers method with the mock function
        self.mock_get_all_users = mocker.patch(
            'views.UsersView.get_all_users',
            return_value=self.users_list
        )

        # Create an instance of UsersView
        self.parent = MainWindow()
        self.users_view = UsersView(parent=self.parent)
        qtbot.addWidget(self.users_view)

    def test_users_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_users.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout, MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout, UserCard) == 3

    def test_users_view_refresh_layout(self, helpers):
        # We remove a user
        self.users_list.pop()

        # Call the refreshLayout method
        self.users_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_users.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout, MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout, UserCard) == 2

    def test_users_view_create_user(self, mocker, helpers):
        # Mock UserDataDialog methods
        mock_inputs = 'John 4', 'test4@testing.com', '1234', 'user'
        mocker.patch.object(UserDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(UserDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_user(name, email, password, role):
            user_4 = User(
                name='John 4',
                email='test4@testing.com',
                password='1234',
                role='user'
            )
            self.users_list.append(user_4)
            return

        mock_create_user = mocker.patch(
            'views.UsersView.create_user',
            side_effect=side_effect_create_user
        )

        # Call the createUser method
        self.users_view.createUser()

        # Validate DB calls
        assert mock_create_user.call_count == 1
        assert self.mock_get_all_users.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout, MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout, UserCard) == 4
