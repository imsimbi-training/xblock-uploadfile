"""A worksheet in structured using HTML/CSS that the student fills out with multiple free text responses."""

import logging
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String, List, Boolean
from xblock.utils.studio_editable import StudioEditableXBlockMixin

from django.core.files.storage import default_storage
from django.http import JsonResponse

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
        default="File Upload",
        scope=Scope.settings,
    )

    file_types = String(
        display_name="File types",
        help="Files that can be uploaded",
        default="*.pdf, *.jpg, *.jpeg, *.png",
        scope=Scope.settings,
    )

    prompt = String(
        display_name="Prompt",
        help="Prompt displayed",
        default="Please upload a file",
        scope=Scope.settings,
    )

    file_info = List(
        default=[],
        scope=Scope.user_state,
        help="A map of the user responses on the worksheet",
    )

    submitted = Boolean(
        default=False,
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

    @XBlock.handler
    def stream_upload(self, request, suffix=''):
        """
        Handle streaming file upload using Django's built-in mechanisms.
        This automatically handles the streaming without explicit chunking.
        """
        if request.method != 'POST':
            return JsonResponse({"result": "error", "message": "Only POST allowed"})

        try:
            # Django automatically handles streaming for file uploads
            # Files are streamed to temporary files automatically
            uploaded_files = []

            for field_name, uploaded_file in request.FILES.items():
                # Process each uploaded file
                file_info = self.process_uploaded_file(uploaded_file)
                uploaded_files.append(file_info)

            self.file_info = uploaded_files
            self.submitted = True
            return JsonResponse({
                "result": "success",
                "files_info": uploaded_files,
                "count": len(uploaded_files)
            })

        except Exception as e:
            return JsonResponse({
                "result": "error",
                "message": str(e)
            })

    def process_uploaded_file(self, uploaded_file):
        """
        Process a single uploaded file that was streamed by Django.
        """
        # Get file metadata
        filename = uploaded_file.name
        file_size = uploaded_file.size
        content_type = uploaded_file.content_type

        # Create full filename
        full_filename = self.full_filename(filename)

        # Save the file - Django handles the streaming internally
        # The uploaded_file is already a file-like object that can be saved directly
        file_path = default_storage.save(full_filename, uploaded_file)
        file_url = default_storage.url(file_path)

        return {
            'user_filename': filename,
            'filename': full_filename,
            'file_path': file_path,
            'file_url': file_url,
            'size': file_size,
            'content_type': content_type
        }
