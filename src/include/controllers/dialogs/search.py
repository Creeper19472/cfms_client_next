"""Controller for the search dialog."""

from typing import TYPE_CHECKING

from include.classes.config import AppShared
from include.controllers.base import BaseController
from include.util.requests import do_request_2

if TYPE_CHECKING:
    from include.ui.controls.dialogs.search import SearchDialog

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class SearchDialogController(BaseController["SearchDialog"]):
    """Controller for handling search operations."""

    def __init__(self, control: "SearchDialog"):
        super().__init__(control)

    async def action_search(self):
        """Execute search with specified parameters."""
        # Get search parameters from the dialog
        query = self.control.search_textfield.value
        
        if not query or not query.strip():
            self.control.search_textfield.error = _("Search query cannot be empty")
            self.control.update()
            return
        
        search_documents = self.control.search_documents_checkbox.value
        search_directories = self.control.search_directories_checkbox.value
        
        if not search_documents and not search_directories:
            self.control.send_error(_("At least one search type must be selected"))
            return
        
        # Get sort parameters
        sort_by_map = {
            _("Name"): "name",
            _("Created time"): "created_time",
            _("Last modified"): "last_modified",
            _("Size"): "size",
        }
        sort_order_map = {
            _("Ascending"): "asc",
            _("Descending"): "desc",
        }
        
        sort_by = sort_by_map.get(self.control.sort_by_dropdown.value, "name")
        sort_order = sort_order_map.get(self.control.sort_order_dropdown.value, "asc")
        
        try:
            limit = int(self.control.limit_textfield.value)
            if limit < 1:
                limit = 100
            if limit > 1000:
                limit = 1000
        except (ValueError, TypeError):
            limit = 100
        
        # Show loading state
        self.control.show_loading()
        
        try:
            # Make the search request
            response = await do_request_2(
                action="search",
                data={
                    "query": query.strip(),
                    "limit": limit,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                    "search_documents": search_documents,
                    "search_directories": search_directories,
                },
                username=self.app_shared.username,
                token=self.app_shared.token,
            )
            
            if response.code == 200:
                # Update results
                self.control.display_results(response.data, query.strip())
            else:
                self.control.send_error(
                    _("Search failed: ({code}) {message}").format(
                        code=response.code,
                        message=response.message,
                    )
                )
                self.control.hide_loading()
        except Exception as e:
            self.control.send_error(f"Search error: {str(e)}")
            self.control.hide_loading()
