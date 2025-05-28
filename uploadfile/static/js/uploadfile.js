function UploadFileXBlock(runtime, element) {
  var dropZone = $("#uploadfile-drop-zone", element);
  var fileInput = $("#uploadfile-input", element);
  var uploadBtn = $("#uploadfile-btn", element);
  var statusDiv = $("#uploadfile-status", element);
  var selectedFiles = null;
  var maxSizeMb = parseInt($(".uploadfile-xblock", element).data('max-size-mb'));
  uploadBtn.hide();
  // Allow clicking the drop zone to trigger file input
  dropZone.on("click", function (e) {
    if (e.target !== fileInput[0] && e.target.tagName !== "A") fileInput.click();
  });

  function showStatus(status) {
    console.log('status', status);
    statusDiv.text(status);
  }

  function refresh(status) {
    $.ajax({
      type: "POST",
      url: runtime.handlerUrl(element, "refresh_content"),
      contentType: "application/json; charset=utf-8",
      data: JSON.stringify({}),
      success: function (response) {
        const { file_html, file_subtext, instructions } = response;
        dropZone.find("#drop-zone-text").html(file_html);
        dropZone.find("#drop-zone-subtext").text(file_subtext);
        dropZone.find("#instructions").text(instructions);
        uploadBtn.hide();
        showStatus(status);
      },
    });
  }

  function filesSelected(files) {
    selectedFiles = files;
    const selectFilesArray = Array.from(selectedFiles);
    const warnings = [];

    for (const file of selectFilesArray) {
      if (file.size > maxSizeMb * 1024 * 1024) {
        warnings.push(file.name);
      }
    }
    if (warnings.length) {
      const warningStatus = `These files are too big: ${warnings.join(", ")}`;
      showStatus(warningStatus);
    }
    if (selectFilesArray && selectFilesArray.length > 0) {
      const names = selectFilesArray.map((o) => o.name).join(", ");
      uploadBtn.show();
      dropZone.find("#drop-zone-text").text(names);
      dropZone.find("#drop-zone-subtext").text("Files uploaded:");
    } else {
      uploadBtn.hide();
      dropZone.find("#drop-zone-text").text("");
      dropZone.find("#drop-zone-subtext").text("");
    }
  }
  // File selected via input
  fileInput.on("change", function (e) {
    showStatus("");
    if (e.target.files.length > 0) {
      filesSelected(e.target.files);
    } else {
      filesSelected(null);
    }
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
    showStatus("");
    filesSelected(files);
  });

  async function uploadFiles() {
    try {
      showStatus("Uploading...");
      // Upload files using Streams API
      // const results = await Promise.all(
      //   Array.from(selectedFiles).map((file) => uploadFileAsStream(file)),
      // );
      await uploadFilesAsStream(selectedFiles)
      refresh();
      selectedFiles = null;
      showStatus("Uploaded successfully!");
      // this.displayResults(results);
    } catch (error) {
      console.log('exception', error);
      refresh();
      showStatus(`Upload failed: ${error.message}`);
    }
  }

  async function uploadFilesAsStream(files) {
    const uploadUrl = runtime.handlerUrl(element, "stream_upload");

    const formData = new FormData();
    for (const file of files) {
      formData.append("files[]", file);
    }
    // formData.append("filename", file.name);
    // formData.append("file_size", file.size);
    // formData.append("file_type", file.type);

    return new Promise((resolve, reject) => {
      $.ajax({
        url: uploadUrl,
        method: "POST",
        data: formData,
        processData: false,  // Don't process FormData
        contentType: false,  // Let browser set content-type
        success: (response) => {
          resolve(response);
        },
        error: (_xhr, _status, error) => {
          console.log('uploadFileAsStream error', error, _status);
          reject(new Error(error || 'Upload failed'));
        }
      });
    });
  }

  uploadBtn.click(function () {
    if (!selectedFiles || selectedFiles.length === 0) {
      showStatus("Please select or drop a file.");
      return;
    }
    uploadFiles();
  });

  function beforeUnload(event) {
    if (selectedFiles) {
      event.preventDefault();
      event.returnValue = "";
    }
  }
  window.addEventListener("beforeunload", beforeUnload);
}
