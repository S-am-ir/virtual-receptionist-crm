"""CRM tools for contact management."""
from .tools import search_contact, add_or_update_contact, add_note_to_contact, create_or_list_tasks

__all__ = [
    "search_contact",
    "add_or_update_contact",
    "add_note_to_contact",
    "create_or_list_tasks"
]
