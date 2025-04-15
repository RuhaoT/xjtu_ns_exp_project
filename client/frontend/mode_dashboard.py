import os

from domain.file_model import DirectViewFileType, ServerFileList, SingleFile
from frontend.utils import DynamicText, HeaderBar
from service.file_service import (FetchServerFileInterface,
                                  FileDownloadInterface, FileDownloadResult,
                                  FileService, FileUploadInterface,
                                  FileUploadResult, LocalFileBackend)
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, Footer, Header, Input, SelectionList,
                             Static, TextArea)
from textual.widgets.selection_list import Selection


class FileSelector(Container):
    """A simple file selector widget."""
    
    

    def compose(self) -> ComposeResult:
        """Compose the file selector widget."""

        self.selection_list = SelectionList[str](
            id="file-selector",
        )
        yield self.selection_list

    def on_mount(self) -> None:
        """Called when the widget is mounted to the screen."""

        self.query_one(SelectionList).border_title = "File Selector"

class FileViewer(Container):
    """A simple file viewer widget."""
    
    text_area_content = reactive("Select a single file to view its content.", init=True, always_update=True)
    highlight_language = reactive(None, init=True, always_update=True)
    
    def compose(self) -> ComposeResult:
        """Compose the file viewer widget."""
        self.current_file_name = DynamicText(id="current-file-name")
        self.current_file_name.text = "No file selected"
        yield self.current_file_name
        
        self.text_area = TextArea.code_editor(text="Select a single file to view its content.",
            id="file-viewer-text-area", language=None)
        yield self.text_area
    
    def watch_text_area_content(self, new_value: str) -> None:
        """Watch for changes in the text area content."""
        text_area = self.query_one("#file-viewer-text-area")
        text_area.text = new_value
        text_area.refresh()
    
    def watch_highlight_language(self, new_value: str) -> None:
        """Watch for changes in the highlight language."""
        text_area = self.query_one("#file-viewer-text-area")
        text_area.language = new_value
        text_area.refresh()

class OperationPanel(Container):
    """A simple operation panel with buttons for actions."""

    def compose(self) -> ComposeResult:
        """Compose the operation panel with buttons."""
        with Horizontal(id="operation-panel-outer-horizontal"):
            with Vertical(id="operation-panel-button-vertical"):
                yield Button("Download", id="download-button", classes="operation-button")
                yield Button("Upload", id="upload-button", classes="operation-button")
                # yield Button("View", id="close-button", classes="operation-button")
                yield Button("Refresh", id="refresh-button", classes="operation-button")
                yield Button("View", id="view-button", classes="operation-button")

            with Vertical(id="operation-panel-input-vertical"):
                yield Static("New file path or directory path:", id="upload-hint")
                self.upload_input = Input(placeholder=f"Current directory: {self.app.   local_file_backend.get_working_directory()}", id="upload-input")
                yield self.upload_input

                yield Static("STATUS:", id="status-hint")
                self.panel_status = DynamicText(id="panel-status")
                self.panel_status.text = "OK"
                yield self.panel_status

class DashboardScreen(Screen):
    """A simple dashboard screen with a placeholder text."""

    def __init__(self):
        super().__init__()
        self.dashboard_text = "Dashboard Screen"
        self.file_service: FileService = self.app.file_service
        self.working_directory: str = self.app.local_file_backend.get_working_directory()

    def compose(self) -> ComposeResult:
        """Compose the dashboard screen."""

        # header & footer
        yield HeaderBar("XJTU NETWORK LAB 2025 CLIENT SERVER", "Client Dashboard")

        with Horizontal(id="dashboard-main-component"):

            # file selector
            self.file_selector = FileSelector(id="server-file-selector")
            self.file_selector.border_title = "File Selector"
            yield self.file_selector

            with Vertical(id="dashboard-content"):
                # file viewer
                self.file_viewer = FileViewer(id="file-viewer")
                self.file_viewer.border_title = "File Viewer"
                yield self.file_viewer
                self.panel_2 =  OperationPanel(
                    id="operation-panel-2",
                )
                self.panel_2.border_title = "Operation Panel"
                yield self.panel_2

        yield Footer()
    
    def action_refresh_file_list(self) -> None:
        """Refresh the file list in the file selector."""
        file_selector: FileSelector = self.query_one(FileSelector)
        # Clear the current selection
        file_selector.selection_list.clear_options()
        
        # Fetch the file list from the server
        request_interface = FetchServerFileInterface(
            current_session=self.app.current_session,
            setting=self.app.current_setting,
        )
        
        current_server_file_list: ServerFileList =self.file_service.fetch_server_file_list(request_interface)
        
        if not current_server_file_list.valid_list:
            # Handle invalid file list
            self.panel_2.panel_status.text = "Failed to fetch file list: " + current_server_file_list.error_message
            return
        
        # Update the file selector with the new file list
        for index, file in enumerate(current_server_file_list.file_list):
            # file_name is the primary key so it should be unique
            file_selector.selection_list.add_option(Selection(file.file_name, file.file_name))
    
    def action_download_file_batch(self, file_names: list[str]) -> None:
    
        if len(file_names) == 0:
            self.panel_2.panel_status.text = "No file selected. Nothing to download."
            return
        else:
            self.panel_2.panel_status.text = f"Downloading {len(file_names)} files:"
            for file_name in file_names:
                self.panel_2.panel_status.text += f"\n- {file_name}"
        
        # Create a file download interface
        download_interface = FileDownloadInterface(
            current_session=self.app.current_session,
            setting=self.app.current_setting,
            file_name_list=file_names,
        )
        
        # Download the files
        download_result: FileDownloadResult = self.file_service.download_file_batch(download_interface)
        
        if not download_result.download_success:
            # Handle download failure
            self.panel_2.panel_status.text = "Download failed: " + download_result.error_message
            return
        else:
            # Handle download success
            self.panel_2.panel_status.text = "Successfully downloaded files:"
            for file_name in download_result.downloaded_file_name_list:
                self.panel_2.panel_status.text += f"\n- {file_name}"
            # find the files that are cached so was not downloaded
            for file_name in file_names:
                if file_name not in download_result.downloaded_file_name_list:
                    self.panel_2.panel_status.text += f"\n- {file_name} (cached)"
            return
    
    def action_upload_file(self, file_or_directory_path: str = None) -> None:
        """Upload a file or directory to the server."""
        # check if the path is none
        if file_or_directory_path == None:
            self.panel_2.panel_status.text = "Please select a file or directory to upload."
            return
        
        # Create a file upload interface
        upload_interface = FileUploadInterface(
            current_session=self.app.current_session,
            setting=self.app.current_setting,
            file_path_or_file_dir_path=file_or_directory_path,
        )
        
        # Upload the file or directory
        upload_result: FileUploadResult = self.file_service.upload_file_batch(upload_interface)
        
        if not upload_result.upload_success:
            # Handle upload failure
            self.panel_2.panel_status.text = "Upload failed: " + upload_result.error_message
            return
        else:
            # Handle upload success
            self.panel_2.panel_status.text = "Successfully uploaded files:"
            for file_name in upload_result.uploaded_file_name_list:
                self.panel_2.panel_status.text += f"\n- {file_name}"
            if upload_result.already_uploaded_file_name_list != None and len(upload_result.already_uploaded_file_name_list) > 0:
                for file_name in upload_result.already_uploaded_file_name_list:
                    self.panel_2.panel_status.text += f"\n- {file_name} (already cached)"
            return
    
    def action_view_file(self, select_file_names: list[str]) -> None:

        file_viewer: FileViewer = self.query_one(FileViewer)

        if len(select_file_names) == 0:
            self.panel_2.panel_status.text = "No file selected. Nothing to view."
            return
        elif len(select_file_names) > 1:
            self.panel_2.panel_status.text = "Please select only one file to view."
            return
            
        # check if the file extension is supported
        file_name = select_file_names[0]
        file_extension = file_name.split(".")[-1]
        match file_extension:
            case DirectViewFileType.TXT:
                file_viewer.highlight_language = None
            case DirectViewFileType.INI:
                file_viewer.highlight_language = None
            case DirectViewFileType.MARKDOWN:
                file_viewer.highlight_language = "markdown"
            case DirectViewFileType.JSON:
                file_viewer.highlight_language = "json"
            case _:
                self.panel_2.panel_status.text = "File type not supported for direct view."
                return
        
        # get the file content from the server
        # make sure the file is downloaded first
        self.action_download_file_batch([file_name])
        
        # fetch file content
        file_path = os.path.join(self.app.current_setting.local_file_dir, file_name)
        file_bytes = self.app.local_file_backend.load_file(file_path)
        
        # decode the file content and display it in the text area
        file_viewer.current_file_name.text = file_name
        file_viewer.text_area_content = file_bytes.decode('utf-8')
        
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the dashboard screen."""
        # Retrieve related components
        file_selector: FileSelector = self.query_one(FileSelector)
        if self.app.current_session == None or self.app.current_setting == None:
            self.panel_2.panel_status.text = "Please login first."
            file_selector.selection_list.clear_options()
            return
        
        # check if the user is logged in
        if event.button.id == "download-button":
            # get the selected file names from the file selector
            select_file_names = file_selector.selection_list.selected
            
            self.action_download_file_batch(select_file_names)

            
        elif event.button.id == "upload-button":
            
            # get the file or directory path from the input
            file_or_directory_path = self.panel_2.upload_input.value
            
            # Upload the file or directory
            self.action_upload_file(file_or_directory_path)
            self.action_refresh_file_list()
            
        elif event.button.id == "refresh-button":
            # Refresh the file list
            self.action_refresh_file_list()
        
        elif event.button.id == "view-button":
            # get the selected file names from the file selector
            select_file_names = file_selector.selection_list.selected
            
            self.action_view_file(select_file_names)
