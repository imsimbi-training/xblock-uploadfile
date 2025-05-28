"""A file upload response for OpenEdx courses."""
import base64
from webob import Response
import json
import uuid
import urllib
from lxml import html as lxml_html

import logging
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean, List, Dict, Integer
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
        default=".pdf, .jpg, .jpeg, .png",
        scope=Scope.settings,
    )

    prompt = String(
        display_name="Prompt",
        help="Prompt displayed",
        default="Please upload a file",
        scope=Scope.settings,
    )

    file_info_list = List(
        default=[],
        scope=Scope.user_state,
        help="A map of the user responses on the worksheet",
    )

    file_info = Dict(
        default={},
        scope=Scope.user_state,
        help="A map of the user responses on the worksheet",
    )

    submitted = Boolean(
        default=False,
        scope=Scope.user_state,
        help="A map of the user responses on the worksheet",
    )

    allow_multiple = Boolean(
        display_name="Allow multiple files",
        help="Alow the student to submit multiple files",
        default=True,
        scope=Scope.settings,
    )

    max_size_mb = Integer(
        display_name="Maximum file size (MB)",
        help="Restrict the size of the uploaded files",
        default=50,
        scope=Scope.settings,
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

    def download_url(self, index):
        return self.runtime.handler_url(self, 'download_file', suffix=str(index))

    def generate_instructions(self):
        if not self.submitted:
            instructions = (
                "Click here or drop a file to upload your response."
                if not self.allow_multiple else "Click here or drop one or more files to upload your response.")
        else:
            instructions = (
                "Click here or drop a file to replace your response."
                if not self.allow_multiple else "Click here or drop one or more files to replace your response.")
        instructions = f"{instructions}. Max allowed file size is {self.max_size_mb}Mb"
        return instructions

    def render_file_html(self):
        # returns (html, subtext) where html is an html snippet for the list of files and the subtext
        # is the intro, e.g. "Files uploaded:"
        file_info_list = self.file_info_list
        # handle legacy single file
        if not file_info_list:
            if self.file_info:
                file_info_list = [self.file_info]
            else:
                file_info_list = []
        file_template = self.resource_string("static/html/file.html")
        file_details = [file_template.format(
            file_url=self.download_url(index), filename=file.get("user_filename"))
            for (index, file) in enumerate(file_info_list)]
        has_file = self.submitted and len(file_info_list) > 0
        subtext = "Files uploaded:" if has_file else ""

        return (",&#32;".join(file_details), subtext)

    def student_view(self, context=None):
        """
        The primary view of the UploadFile, shown to students
        when viewing courses.
        """
        (file_html, subtext) = self.render_file_html()
        multiple = "multiple" if self.allow_multiple else ""
        instructions = self.generate_instructions()
        html = self.resource_string("static/html/uploadfile.html").format(
            prompt=self.prompt,
            subtext=subtext,
            file_types=self.file_types,
            filename=file_html,
            submitted="true" if self.submitted else "false",
            state_class=self.state_class(),
            multiple=multiple,
            instructions=instructions,
            max_size_mb=self.max_size_mb
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
        return f"xblock_uploadfile/{user_id}/{uuid.uuid4()}"

    @XBlock.json_handler
    def refresh_content(self, data, suffix=''):
        # if we use context in the future, then we must pass it here
        log.debug(
            "refresh_content %s", data)
        instructions = self.generate_instructions()
        (html, subtext) = self.render_file_html()
        return {'success': True, 'file_html': html, "file_subtext": subtext, "instructions": instructions}

    @XBlock.json_handler
    def upload_file(self, data, suffix=''):
        """
        Receives file uploads from the JS frontend, stores the file, and records submission.
        This is a non-streaming, non-chnunking version
        """
        log.debug(
            "upload_file %s", data)
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

    @XBlock.handler
    def download_file(self, request, suffix=''):
        """Secure file download with authentication"""
        log.debug('download_file called with suffix: %s', suffix)

        try:
            # Get file index from URL suffix (e.g., /0, /1, /2)
            file_index = 0
            if suffix and suffix.strip('/').isdigit():
                file_index = int(suffix.strip('/'))

            # Get file list (handle both legacy single file and new multiple files)
            file_info_list = self.file_info_list
            if not file_info_list and self.file_info:
                # Handle legacy single file
                file_info_list = [self.file_info]

            if not file_info_list or file_index >= len(file_info_list):
                log.warning("Download attempt with invalid file index %s: %s",
                            file_index, self.scope_ids.usage_id)
                response = Response(status=404)
                response.text = "File not found"
                return response

            file_info = file_info_list[file_index]
            content_type = file_info.get(
                'content_type', 'application/octet-stream')
            user_filename = file_info.get('user_filename', 'download.bin')
            file_path = file_info['file_path']

            if not default_storage.exists(file_path):
                log.warning("File does not exist in storage: %s", file_path)
                response = Response(status=404)
                response.text = "File not found"
                return response

            # Read file content
            file_content = default_storage.open(file_path).read()
            encoded_filename = urllib.parse.quote(user_filename)

            # Create WebOb response with proper headers
            response = Response(
                body=file_content,
                content_type=content_type
            )

            # Set Content-Disposition header for download with proper filename
            response.headers['Content-Disposition'] = f'attachment; filename="{user_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            response.headers['Content-Length'] = str(len(file_content))

            # Disable caching
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

            log.debug('download_file: serving %s bytes as %s',
                      len(file_content), user_filename)
            return response

        except Exception as e:
            log.exception("Error downloading file: %s", str(e))
            response = Response(status=500)
            response.text = f"Error downloading file: {str(e)}"
            return response

    @staticmethod
    def workbench_scenarios():
        """canned scenarios for display in the workbench."""
        return [
            (
                "UploadFileBlock1",
                """
                    <uploadfile
                        display_name="File Upload 1"
                        prompt="Upload a file to test this out"
                        max_size_mb="20"
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
        Because it is form data we must use webob responses and webob request.
        """
        log.debug("stream_upload: entry")
        if request.method != 'POST':
            log.debug("stream_upload: not POST")
            return Response(json.dumps({"result": "error", "message": "Only POST allowed"}), content_type='application/json; charset=utf-8', status=400)

        try:
            log.debug("stream_upload: POST")
            uploaded_files = []

            # WebOb request - access files through POST property
            log.debug("stream_upload: POST vars %s", request.POST)

            files = request.POST.getall('files[]')
            if not isinstance(files, list):
                # only when when there is more than one, is it in a list
                files = [files]
            log.debug("stream_upload: files %s %s", files, type(files))
            for file_var in files:
                file = file_var.file
                if (file.size <= self.max_size_mb * 1024 * 1024):
                    log.debug('stream_upload file %s; %s', file, dir(file))
                    file_info = self.process_uploaded_file(file)
                    # In WebOb, uploaded files are in request.POST
                    uploaded_files.append(file_info)
                else:
                    log.error("File size too big %d, %s, (%d)",
                              file.size, file.name, self.max_size_mb)

            self.file_info_list = uploaded_files
            self.submitted = True

            return Response(json.dumps({
                "result": "success",
                "files_info": uploaded_files,
                "count": len(uploaded_files)
            }), content_type='application/json; charset=utf-8')

        except Exception as e:
            log.exception("Error in stream_upload: %s", str(e))
            return Response(json.dumps({"result": "error", "message": str(e)}), content_type='application/json; charset=utf-8', status=500)

    def process_uploaded_file(self, file):
        """
        Process a single uploaded file that was streamed by Django.
        """
        # Get file metadata
        filename = file.name
        size = file.size
        content_type = file.content_type

        # Create full filename
        full_filename = self.full_filename(filename)

        # Save the file - Django handles the streaming internally
        # The uploaded_file is already a file-like object that can be saved directly
        file_path = default_storage.save(full_filename, file)
        file_url = default_storage.url(file_path)

        result = {
            'user_filename': filename,
            'filename': full_filename,
            'file_path': file_path,
            'size': size,
            'content_type': content_type,
            'file_url': file_url
        }
        log.debug("stream_upload: result %s", result)
        return result
