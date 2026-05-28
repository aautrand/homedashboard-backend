from datetime import date
from unittest.mock import MagicMock

import pytest

from dashboard.src.calendars.models.todo import Todo
from dashboard.src.calendars.todo_manager import TodoManager


class TestTodoManager:
    """Tests for the TodoManager class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock SQLAlchemy session."""
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        """Create a TodoManager with a mock db session."""
        return TodoManager(mock_db)

    def test_init_stores_db(self, mock_db):
        """Test that the manager stores the db session."""
        manager = TodoManager(mock_db)
        assert manager.db is mock_db

    def test_add_todo(self, manager, mock_db):
        """Test adding a new todo."""
        manager.add_todo(title="Buy groceries")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        added_todo = mock_db.add.call_args[0][0]
        assert added_todo.title == "Buy groceries"
        assert added_todo.active is True

    def test_add_todo_inactive(self, manager, mock_db):
        """Test adding a todo with active=False."""
        manager.add_todo(title="Old task", active=False)

        added_todo = mock_db.add.call_args[0][0]
        assert added_todo.title == "Old task"
        assert added_todo.active is False

    def test_get_todo(self, manager, mock_db):
        """Test getting a todo by ID."""
        mock_todo = MagicMock(spec=Todo)
        mock_db.get.return_value = mock_todo

        result = manager.get_todo(1)

        mock_db.get.assert_called_once_with(Todo, 1)
        assert result is mock_todo

    def test_get_todo_not_found(self, manager, mock_db):
        """Test getting a non-existent todo returns None."""
        mock_db.get.return_value = None

        result = manager.get_todo(999)

        assert result is None

    def test_get_all_todos(self, manager, mock_db):
        """Test getting all todos."""
        mock_todos = [MagicMock(spec=Todo), MagicMock(spec=Todo)]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_todos

        result = manager.get_all_todos()

        assert result == mock_todos
        mock_db.execute.assert_called_once()

    def test_get_active_todos(self, manager, mock_db):
        """Test getting only active todos."""
        mock_todos = [MagicMock(spec=Todo)]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_todos

        result = manager.get_active_todos()

        assert result == mock_todos

    def test_get_todos_by_status_active(self, manager, mock_db):
        """Test filtering todos by active=True."""
        mock_todos = [MagicMock(spec=Todo)]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_todos

        result = manager.get_todos_by_status(True)

        assert result == mock_todos

    def test_get_todos_by_status_inactive(self, manager, mock_db):
        """Test filtering todos by active=False."""
        mock_todos = [MagicMock(spec=Todo)]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_todos

        result = manager.get_todos_by_status(False)

        assert result == mock_todos

    def test_update_todo(self, manager, mock_db):
        """Test updating a todo's fields."""
        mock_todo = MagicMock(spec=Todo)
        mock_todo.title = "Old title"
        mock_todo.active = True
        mock_db.get.return_value = mock_todo

        result = manager.update_todo(1, title="New title", active=False)

        mock_db.get.assert_called_once_with(Todo, 1)
        assert mock_todo.title == "New title"
        assert mock_todo.active is False
        mock_db.commit.assert_called_once()
        assert result is mock_todo

    def test_update_todo_not_found(self, manager, mock_db):
        """Test updating a non-existent todo returns None."""
        mock_db.get.return_value = None

        result = manager.update_todo(999, title="Won't work")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_todo_ignores_unknown_fields(self, manager, mock_db):
        """Test that update_todo ignores fields not on the model."""
        mock_todo = MagicMock(spec=Todo)
        mock_todo.title = "Title"
        mock_db.get.return_value = mock_todo

        # hasattr on MagicMock(spec=Todo) returns False for non-existent attrs
        result = manager.update_todo(1, nonexistent_field="value")

        assert result is mock_todo
        mock_db.commit.assert_called_once()

    def test_delete_todo(self, manager, mock_db):
        """Test deleting a todo."""
        mock_todo = MagicMock(spec=Todo)
        mock_db.get.return_value = mock_todo

        result = manager.delete_todo(1)

        mock_db.get.assert_called_once_with(Todo, 1)
        mock_db.delete.assert_called_once_with(mock_todo)
        mock_db.commit.assert_called_once()
        assert result is mock_todo

    def test_delete_todo_not_found(self, manager, mock_db):
        """Test deleting a non-existent todo returns None."""
        mock_db.get.return_value = None

        result = manager.delete_todo(999)

        assert result is None
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_mark_todo_shown(self, manager, mock_db):
        """Test marking a todo as shown on a specific date."""
        mock_todo = MagicMock(spec=Todo)
        mock_db.get.return_value = mock_todo
        shown_date = date(2025, 8, 15)

        result = manager.mark_todo_shown(1, shown_date)

        assert mock_todo.last_shown_date == shown_date
        mock_db.commit.assert_called_once()
        assert result is mock_todo

    def test_mark_todo_shown_not_found(self, manager, mock_db):
        """Test marking a non-existent todo as shown returns None."""
        mock_db.get.return_value = None

        result = manager.mark_todo_shown(999, date(2025, 8, 15))

        assert result is None
        mock_db.commit.assert_not_called()
