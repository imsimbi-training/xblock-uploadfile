function UploadFileXBlock(runtime, element) {
  var dropZone = element.find("#drop-zone");
  var fileInput = element.find("#upload-file-input");
  var uploadBtn = element.find("#upload-file-btn");
  var statusDiv = element.find("#upload-status");
  var selectedFiles = null;

  // Allow clicking the drop zone to trigger file input
  dropZone.on("click", function () {
    fileInput.click();
  });

  function showStatus(status) {
    statusDiv.text(status);
  }

  function setFiles(files) {
    selectedFiles = files;
    const content = files ? files.map((f) => f.name) : "";
    dropZone.find("#drop-zone-text").text(content);
  }

  // File selected via input
  fileInput.on("change", function (e) {
    if (e.target.files.length > 0) {
      setFiles(e.target.files);
    } else {
      setFiles();
    }
    showStatus("");
  });

  // Handle drag over
  dropZone.on("dragover", function (e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.addClass("dragover");
  });
  dropZone.on("dragleave drop", function (e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.removeClass("dragover");
  });

  // Handle dropped files
  dropZone.on("drop", function (e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.removeClass("dragover");
    var files = e.originalEvent.dataTransfer.files;
    setFiles(files);
    showStatus("");
  });

  function uploadFilesNonStream() {
    var reader = new FileReader();
    reader.onload = function (e) {
      runtime.notify("save", { state: "start" });
      $.ajax({
        type: "POST",
        url: runtime.handlerUrl(element, "upload_file"),
        data: JSON.stringify({
          file_name: selectedFile.name,
          file_data: btoa(e.target.result),
        }),
        contentType: "application/json; charset=utf-8",
        success: function (response) {
          showStatus("Upload successful!");
          runtime.notify("save", { state: "end" });
          if (response.file_url) {
            element
              .find("#uploaded-file")
              .html(
                '<a href="' +
                  response.file_url +
                  '" target="_blank">View uploaded file</a>',
              );
          }
        },
      });
    };
    reader.readAsBinaryString(selectedFile);
  }

  async function uploadFilesStream(selectedFiles) {
    try {
      showStatus("Starting upload...");

      // Upload files using Streams API
      const results = await Promise.all(
        Array.from(selectedFiles).map((file) => uploadFileAsStream(file)),
      );

      showStatus("Uploaded successfully!");
      // this.displayResults(results);
    } catch (error) {
      showStatus(`Upload failed: ${error.message}`);
    }
  }

  async function uploadFileAsStream(file) {
    // Create a readable stream from the file
    const fileStream = file.stream();

    // Get upload URL from backend
    const uploadUrl = this.runtime.handlerUrl(this.element, "stream_upload");

    // Create FormData with the file
    const formData = new FormData();
    formData.append("file", file);
    formData.append("filename", file.name);
    formData.append("file_size", file.size);
    formData.append("file_type", file.type);

    // Use fetch with streaming
    const response = await fetch(uploadUrl, {
      method: "POST",
      body: formData, // FormData automatically streams the file
      headers: {
        // "X-CSRFToken": this.getCSRFToken(), // Add CSRF if needed
      },
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  }

  uploadBtn.click(function () {
    if (!selectedFiles || selectedFiles.length === 0) {
      showStatus("Please select or drop a file.");
      return;
    }
    uploadFilesNonStream();
  });
}
