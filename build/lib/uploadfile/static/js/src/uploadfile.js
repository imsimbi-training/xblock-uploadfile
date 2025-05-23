function UploadFileXBlock(runtime, element) {
  var dropZone = element.find("#drop-zone");
  var fileInput = element.find("#upload-file-input");
  var uploadBtn = element.find("#upload-file-btn");
  var statusDiv = element.find("#upload-status");
  var selectedFile = null;

  // Allow clicking the drop zone to trigger file input
  dropZone.on("click", function () {
    fileInput.click();
  });

  // File selected via input
  fileInput.on("change", function (e) {
    if (fileInput[0].files.length > 0) {
      selectedFile = fileInput[0].files[0];
      dropZone.find("#drop-zone-text").text(selectedFile.name);
      statusDiv.text("");
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
      selectedFile = files[0];
      dropZone.find("#drop-zone-text").text(selectedFile.name);
      statusDiv.text("");
    }
  });

  uploadBtn.click(function () {
    if (!selectedFile) {
      statusDiv.text("Please select or drop a file.");
      return;
    }
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
          statusDiv.text("Upload successful!");
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
  });
}
