import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.UserCard import UserCard
from components.dialogs.UserDataDialog import UserDataDialog
from core.database.models import User
from views.UsersView import UsersView


class TestUserCard:
    user = User(name='John Doe', email='test@testing.com', password='1234', role='user')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(UsersView, 'refreshLayout')

        self.parent = UsersView()
        self.user.id = 1
        self.card = UserCard(self.user, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_user_card_init(self):
        assert self.card.user == self.user
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_user_card_update_user(self, mocker, dialogResponse, expected_updated):
        # Mock UserDataDialog methods
        mock_input = 'Updated Name', 'updated@email.com', 'updatedpassword', 'admin'
        mocker.patch.object(UserDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(UserDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_user = mocker.patch('components.cards.UserCard.update_user')

        # Call the updateUser method
        self.card.updateUser()

        # Validate DB calls
        assert mock_update_user.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_user_params = {
                'id': 1,
                'name': 'Updated Name',
                'email': 'updated@email.com',
                'role': 'admin'
            }
            mock_update_user.assert_called_with(*update_user_params.values())

    def test_user_card_update_user_db_error(self, mocker):
        # Mock UserDataDialog methods
        mock_input = 'Updated Name', 'updated@email.com', 'updatedpassword', 'admin'
        mocker.patch.object(UserDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(UserDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_user = mocker.patch(
            'components.cards.UserCard.update_user',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the updateUser method
        self.card.updateUser()

        # Validate DB calls
        assert mock_update_user.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_user_card_remove_user(self, mocker, msgBoxResponse, expectedMethodCalls):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_user = mocker.patch('components.cards.UserCard.remove_user')

        # Call the removeUser method
        self.card.removeUser()

        # Validate DB calls
        assert mock_remove_user.call_count == expectedMethodCalls

    def test_user_card_remove_user_db_error(self, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_user = mocker.patch(
            'components.cards.UserCard.remove_user',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeUser method
        self.card.removeUser()

        # Validate DB calls
        assert mock_remove_user.call_count == 1
        assert mock_popup.call_count == 1
