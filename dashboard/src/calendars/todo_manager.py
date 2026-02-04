from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.src.calendars.models.todo import Todo


class TodoManager:
    def __init__(self, db: Session):
        self.db = db

    def add_todo(self, title: str, active: bool = True):
        """Add a new todo."""
        todo = Todo(title=title, active=active)
        self.db.add(todo)
        self.db.commit()
        return todo

    def get_todo(self, todo_id: int):
        """Get a specific todo by ID."""
        return self.db.get(Todo, todo_id)

    def get_all_todos(self):
        """Get all todos."""
        stmt = select(Todo)
        return self.db.execute(stmt).scalars().all()

    def get_active_todos(self):
        """Get all active todos."""
        stmt = select(Todo).where(Todo.active == True)
        return self.db.execute(stmt).scalars().all()

    def get_todos_by_status(self, active: bool):
        """Get todos filtered by active status."""
        stmt = select(Todo).where(Todo.active == active)
        return self.db.execute(stmt).scalars().all()

    def update_todo(self, todo_id: int, **kwargs):
        """Update a todo."""
        todo = self.db.get(Todo, todo_id)
        if todo:
            for key, value in kwargs.items():
                if hasattr(todo, key):
                    setattr(todo, key, value)
            self.db.commit()
        return todo

    def delete_todo(self, todo_id: int):
        """Delete a todo."""
        todo = self.db.get(Todo, todo_id)
        if todo:
            self.db.delete(todo)
            self.db.commit()
        return todo

    def mark_todo_shown(self, todo_id: int, shown_date: date):
        """Mark a todo as shown on a specific date."""
        todo = self.db.get(Todo, todo_id)
        if todo:
            todo.last_shown_date = shown_date
            self.db.commit()
        return todo
