function UploadFileXBlock(runtime, element) {
  console.log("UploadFileXBlock", runtime, element);
  var dropZone = $("#uploadfile-drop-zone", element);
  var fileInput = $("#uploadfile-input", element);
  var uploadBtn = $("#uploadfile-btn", element);
  var statusDiv = $("#uploadfile-status", element);
  var downloadDiv = $("#uploadfile-download", element);
  var selectedFile = null;

  console.log("uploadBtn", uploadBtn);
  uploadBtn.hide();
  // Allow clicking the drop zone to trigger file input
  dropZone.on("click", function (e) {
    if (e.target !== fileInput[0]) fileInput.click();
  });

  function fileSelected(file) {
    selectedFile = file;
    uploadBtn.show();
    dropZone.find("#drop-zone-text").text(file.name);
    statusDiv.text("");
  }
  // File selected via input
  fileInput.on("change", function (e) {
    if (fileInput.length > 0 && fileInput[0].files.length > 0) {
      fileSelected(fileInput[0].files[0]);
    } else {
      uploadBtn.hide();
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
    if (files.length > 0) {
      fileSelected(files[0]);
    }
  });

  uploadBtn.click(function () {
    if (!selectedFile) {
      statusDiv.text("Please select or drop a file.");
      return;
    }
    var reader = new FileReader();
    reader.onload = function (e) {
      $.ajax({
        type: "POST",
        url: runtime.handlerUrl(element, "upload_file"),
        data: JSON.stringify({
          filename: selectedFile.name,
          file_data: btoa(e.target.result),
          file_size: selectedFile.size,
          file_type: selectedFile.type,
        }),
        contentType: "application/json; charset=utf-8",
        success: function (response) {
          statusDiv.text("Upload successful!");
          downloadDiv.show();
          var file_url = response.file_info.file_url;
          downloadDiv.find("a").attr("href", file_url);
        },
      });
      uploadBtn.hide();
      selectedFile = null;
    };
    reader.readAsBinaryString(selectedFile);
  });

  function beforeUnload(event) {
    if (selectedFile) {
      event.preventDefault();
      event.returnValue = "";
    }
  }
  window.addEventListener("beforeunload", beforeUnload);
}
