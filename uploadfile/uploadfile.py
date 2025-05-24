"""A file upload response for OpenEdx courses."""
import base64
import urllib
from lxml import html as lxml_html
from django.http import HttpResponse, Http404

import logging
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean, Dict
from xblock.utils.studio_editable import StudioEditableXBlockMixin
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

log = logging.getLogger(__name__)


class UploadFileBlock(StudioEditableXBlockMixin, XBlock):
    """
    Prompts the user to upload a file. Allows for download and reupload.
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
        default=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,image/*",
        scope=Scope.settings,
    )

    prompt = String(
        display_name="Prompt",
        help="Prompt displayed",
        default="Please upload a file",
        scope=Scope.settings,
    )

    submitted = Boolean(
        scope=Scope.user_state,
        help="True if the user has submitted a file",
        default=False
    )

    file_info = Dict(
        default={},
        scope=Scope.user_state,
        help="Student uploaded files metadata"
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def state_class(self):
        if self.submitted:
            return "state-uploaded"
        return "state-empty"
    # Displays the upload prompt

    def student_view(self, context=None):
        """
        The primary view of the UploadFile, shown to students
        when viewing courses.
        """
        file_info = self.file_info
        has_file = self.submitted and file_info.get('file_url')
        user_filename = file_info.get("user_filename", "")
        subtext = "File uploaded:" if user_filename else ""
        html = self.resource_string("static/html/uploadfile.html").format(
            prompt=self.prompt,
            subtext=subtext,
            file_url=file_info.get("file_url", ""),
            file_types=self.file_types,
            filename=user_filename,
            submitted="true" if file_info.get("submitted", False) else "false",
            state_class=self.state_class(),
            download_display='none' if not has_file else 'inline-block'
        )

        # Parse HTML and add accept attribute to file inputs
        try:
            # Parse the HTML
            doc = lxml_html.fromstring(html)

            # Find all input elements with type="file"
            file_inputs = doc.xpath('//input[@type="file"]')

            # Add accept attribute to each file input
            for file_input in file_inputs:
                file_input.set('accept', self.file_types)

            # Convert back to string
            html = lxml_html.tostring(doc, encoding='unicode')

        except Exception as e:
            # If parsing fails, log the error and use original HTML
            log.warning(
                "Failed to parse HTML for adding accept attribute %s", e)

        frag = Fragment(html)
        frag.add_css(self.resource_string("static/css/uploadfile.css"))
        frag.add_javascript(self.resource_string("static/js/uploadfile.js"))
        frag.initialize_js('UploadFileXBlock')
        return frag

    def full_filename(self, filename):
        user_id = self.runtime.user_id
        return f"xblock_uploadfile/{user_id}/{filename}"

    @ XBlock.json_handler
    def upload_file(self, data, suffix=''):
        """
        Receives file uploads from the JS frontend, stores the file, and records submission.
        """
        file_data_base64 = data['file_data']
        filename = data['filename']
        file_size = data['file_size']
        file_type = data['file_type']

        binary_data = base64.b64decode(file_data_base64)

        # Create a ContentFile from the binary data
        content_file = ContentFile(binary_data)
        # Save the file with Django's storage system
        full_filename = self.full_filename(filename)
        file_path = default_storage.save(full_filename, content_file)
        file_url = default_storage.url(file_path)

        self.file_info = {
            'user_filename': filename,
            'filename': full_filename,
            'file_path': file_path,
            'file_url': file_url,
            'size': file_size,
            'content_type': file_type
        }
        file_url = default_storage.url(file_path)

        # Store the file (this uses student state storage
        # Save the file reference
        self.submitted = True
        return {"result": "success", "file_info": self.file_info}

    @ XBlock.handler
    def download_file(self, request, suffix=''):
        """Secure file download with authentication"""
        print('download_file')
        # Check if user has access to this file
        try:
            file_info = self.file_info
            if not file_info:
                log.warning("Download attempt with no file: %s",
                            self.scope_ids.usage_id)
                raise Http404("File not found")
            content_type = file_info.get(
                'content_type', 'application/octet-stream')

            user_filename = file_info.get('user_filename', 'download.bin')

            # Securely serve the file
            file_path = file_info['file_path']

            if not default_storage.exists(file_path):
                log.warning("File does not exist in storage: %s", file_path)
                raise Http404("File not found")

            # Read file content
            file_content = default_storage.open(file_path).read()
            encoded_filename = urllib.parse.quote(user_filename)
            # Create secure response
            response = HttpResponse(
                file_content,
                content_type=content_type
            )

            # Set appropriate headers

            print('download_file', len(file_content), user_filename)
            response['Content-Disposition'] = f'attachment; filename="{user_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            response['Content-Length'] = len(file_content)

            # Disable caching to prevent issues
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            print('headers', response.headers)
            return response

        except Exception as e:
            print('download_file exc', e)
            log.exception("Error downloading file: %s", str(e))
            return HttpResponse(f"Error downloading file: {str(e)}", status=500)

    @ staticmethod
    def workbench_scenarios():
        """canned scenarios for display in the workbench."""
        return [
            (
                "UploadFileBlock1",
                """
                    <uploadfile
                        display_name="File Upload 1"
                        prompt="Upload a file to test this out"
                    >
                    </uploadfile>
                    """,
            ),
        ]
