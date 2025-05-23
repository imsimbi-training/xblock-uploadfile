"""A worksheet in structured using HTML/CSS that the student fills out with multiple free text responses."""

import importlib
import logging
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Dict, Scope, String
from xblock.utils.studio_editable import StudioEditableXBlockMixin

from copy import deepcopy

log = logging.getLogger(__name__)


class WorksheetBlock(StudioEditableXBlockMixin, XBlock):
    """
    An HTML worksheet with sections to be filled in by a student.
    Typically it could be in the structure of a table or other graphical structure
    of organising information
    """

    editable_fields = [
        "display_name",
        "file_types",
        "prompt",
    ]

    display_name = String(
        display_name="Display Name",
        help="This is the title for this question type",
        default="File Upload",  # type: ignore
        scope=Scope.settings,
    )

    file_types = String(
        display_name="File types",
        help="Files that can be uploaded",
        default="*.pdf, *.jpg, *.jpeg, *.png",  # type: ignore
        scope=Scope.settings,
    )

    prompt = String(
        display_name="Prompt",
        help="Prompt displayed",
        default="Please upload a file",
        scope=Scope.settings,
    )

    student_answer = Dict(
        default={"submitted": False},  # type: ignore
        scope=Scope.user_state,
        help="A map of the user responses on the worksheet",
    )

    # Displays the worksheet
    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        The primary view of the UploadFile, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/uploadfile.html").format(
            prompt=self.prompt,
            file_url=self.file_url,
            submitted="true" if self.submitted else "false",
        )
        frag = Fragment(html)
        frag.add_css(self.resource_string("static/css/uploadfile.css"))
        frag.add_javascript(self.resource_string("static/js/uploadfile.js"))
        frag.initialize_js('UploadFileXBlock')
        return frag

    @XBlock.json_handler
    def upload_file(self, data, suffix=''):
        """
        Receives file uploads from the JS frontend, stores the file, and records submission.
        """
        file_data = data['file_data']
        file_name = data['file_name']

        # Store the file (this uses student state storage)
        file_storage = self.runtime.student_file_storage(self)
        file_storage.save(file_name, file_data.encode(
            'latin1'))  # decode if needed

        # Save the file reference
        self.file_url = self.runtime.handler_url(
            self, 'get_file', suffix=file_name)
        self.submitted = True
        return {"result": "success", "file_url": self.file_url}

    @XBlock.handler
    def get_file(self, request, suffix=''):
        """
        Returns the uploaded file for download/display.
        """
        file_storage = self.runtime.student_file_storage(self)
        file = file_storage.open(suffix, 'rb')
        response = request.Response(file.read())
        # You may want to add headers here for content-type, etc.
        return response

    @staticmethod
    def workbench_scenarios():
        """canned scenarios for display in the workbench."""
        return [
            (
                "WorksheetBlock1",
                """
                    <uploadfile
                        display_name="Test 1"
                        html_url="https://imsimbi-documents-public.s3.amazonaws.com/workbooks/uploadfile.html"
                        initial_repeats="2"
                    >
                    </uploadfile>
                    """,
            ),
        ]
