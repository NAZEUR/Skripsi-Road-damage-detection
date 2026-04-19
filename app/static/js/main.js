// Road Damage Detection - Complete JavaScript
let uploadedFilePath = null,
  uploadedFileName = null,
  outputImagePath = null,
  outputJSONPath = null,
  appConfig = null,
  zoomLevel = 1,
  imageQueue = [],
  historyPNGs = [],
  historyJSONs = [],
  isProcessingQueue = false,
  appSessionStats = {
    imagesProcessed: 0,
    totalDefects: 0,
    confidenceSum: 0,
    timeSum: 0,
    categories: {
      "D40 - Pothole": 0,
      "D00 - Longitudinal Crack": 0,
      "D10 - Transverse Crack": 0,
      "D20 - Alligator Crack": 0,
    },
  };

document.addEventListener("DOMContentLoaded", initApp);
async function initApp() {
  try {
    await loadConfig();
    initSidebarStates();
    initThemeState();
    setupEventListeners();
    setupFileUpload();
    setupSliders();
    setupDetectionMode();
  } catch (error) {
    console.error("Init error:", error);
  }
}
async function loadConfig() {
  const response = await fetch("/config");
  const data = await response.json();
  if (data.success) appConfig = data.data;
}

function setupEventListeners() {
  document
    .getElementById("fileInput")
    .addEventListener("change", handleFileSelect);
}
function setupFileUpload() {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      handleFileSelect({ target: fileInput });
    }
  });
}
function setupSliders() {
  const confSlider = document.getElementById("confidenceSlider");
  const confValue = document.getElementById("confidenceValue");
  confSlider.addEventListener("input", () => {
    confValue.textContent = confSlider.value;
  });
  const sliceSlider = document.getElementById("sliceSizeSlider");
  const sliceValue = document.getElementById("sliceSizeValue");
  sliceSlider.addEventListener("input", () => {
    sliceValue.textContent = sliceSlider.value;
  });
  const overlapSlider = document.getElementById("overlapSlider");
  const overlapValue = document.getElementById("overlapValue");
  overlapSlider.addEventListener("input", () => {
    overlapValue.textContent = parseFloat(overlapSlider.value).toFixed(2);
  });
  const matchSlider = document.getElementById("matchSlider");
  const matchValue = document.getElementById("matchValue");
  matchSlider.addEventListener("input", () => {
    matchValue.textContent = parseFloat(matchSlider.value).toFixed(2);
  });
}
function setupDetectionMode() {
  const radios = document.querySelectorAll('input[name="detectionMode"]');
  radios.forEach((radio) => {
    radio.addEventListener("change", () => {
      const sahiParams = document.getElementById("sahiParams");
      if (radio.value === "sahi") {
        sahiParams.classList.remove("d-none");
      } else {
        sahiParams.classList.add("d-none");
      }
    });
  });
}
async function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  if (!validateFile(file)) return;
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch("/upload", { method: "POST", body: formData });
    const data = await response.json();
    if (data.success) {
      if (data.data.is_zip) {
        imageQueue = data.data.extracted_files;
        document.getElementById("fileName").textContent =
          data.data.filename + ` (${imageQueue.length} files)`;
        document.getElementById("fileSize").textContent =
          data.data.size + " MB";
        document.getElementById("fileResolution").textContent = "ZIP Archive";
        document.getElementById("fileInfo").classList.remove("d-none");
        document.getElementById("runAnalysisBtn").disabled = false;

        document.getElementById("emptyState").style.display = "none";
        document.getElementById("originalImage").classList.add("d-none");
      } else {
        uploadedFilePath = data.data.filepath;
        uploadedFileName = data.data.filename;
        showImagePreview(file, data.data);
        document.getElementById("runAnalysisBtn").disabled = false;
        imageQueue = [
          { filepath: uploadedFilePath, filename: uploadedFileName },
        ];
      }
    } else {
      alert("Upload failed: " + data.error);
    }
  } catch (error) {
    console.error("Upload error:", error);
    alert("Upload failed: " + error.message);
  }
}
function validateFile(file) {
  const allowedTypes = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "application/zip",
    "application/x-zip-compressed",
    "multipart/x-zip",
  ];
  if (
    !allowedTypes.includes(file.type) &&
    !file.name.toLowerCase().endsWith(".zip")
  ) {
    alert("Invalid file type. Please upload JPG, PNG, BMP, or ZIP");
    return false;
  }
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    alert("File too large. Maximum 50MB");
    return false;
  }
  return true;
}
function showImagePreview(file, fileData) {
  const reader = new FileReader();
  reader.onload = function (e) {
    const img = document.getElementById("originalImage");
    img.src = e.target.result;
    img.classList.remove("d-none");
    document.getElementById("emptyState").style.display = "none";
  };
  reader.readAsDataURL(file);
  document.getElementById("fileName").textContent = fileData.filename;
  document.getElementById("fileSize").textContent = fileData.size + " MB";
  document.getElementById("fileResolution").textContent = fileData.resolution;
  document.getElementById("fileInfo").classList.remove("d-none");
}
function clearUpload() {
  uploadedFilePath = null;
  uploadedFileName = null;
  outputImagePath = null;
  outputJSONPath = null;
  imageQueue = [];
  document.getElementById("fileInput").value = "";
  document.getElementById("originalImage").classList.add("d-none");
  document.getElementById("resultImage").classList.add("d-none");
  document.getElementById("emptyState").style.display = "block";
  document.getElementById("resultEmptyState").style.display = "block";
  document.getElementById("fileInfo").classList.add("d-none");
  document.getElementById("runAnalysisBtn").disabled = true;
  disableExportButtons();
}
async function runDetection() {
  if (!imageQueue || imageQueue.length === 0) {
    alert("Please upload an image or zip first");
    return;
  }
  if (isProcessingQueue) return;
  isProcessingQueue = true;
  document.getElementById("runAnalysisBtn").disabled = true;

  try {
    const mode = document.querySelector(
      'input[name="detectionMode"]:checked',
    ).value;
    const confidence =
      parseFloat(document.getElementById("confidenceSlider").value) / 100;
    const paramsTemplate = { mode: mode, confidence: confidence };
    if (mode === "sahi") {
      paramsTemplate.slice_height = parseInt(
        document.getElementById("sliceSizeSlider").value,
      );
      paramsTemplate.slice_width = parseInt(
        document.getElementById("sliceSizeSlider").value,
      );
      paramsTemplate.overlap_ratio = parseFloat(
        document.getElementById("overlapSlider").value,
      );
      paramsTemplate.match_threshold = parseFloat(
        document.getElementById("matchSlider").value,
      );
    }
    showLoading();

    // Process queue sequentially
    for (let i = 0; i < imageQueue.length; i++) {
      const item = imageQueue[i];
      const loadingText = document.querySelector(".loading-text");

      let originalText = loadingText.getAttribute("data-original");
      if (!originalText) {
        originalText = loadingText.textContent;
        loadingText.setAttribute("data-original", originalText);
      }
      loadingText.textContent = `Processing (${i + 1}/${imageQueue.length})...`;

      const params = { ...paramsTemplate, filepath: item.filepath };

      try {
        console.log("Sending detection request:", params);
        const response = await fetch("/detect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Detection response:", data);

        if (!data.success) {
          throw new Error(data.error || "Detection failed with unknown error");
        }

        if (data.data && data.data.output) {
          historyPNGs.push(data.data.output.image);
          historyJSONs.push(data.data.output.json);
          outputImagePath = data.data.output.image;
          outputJSONPath = data.data.output.json;

          await new Promise((resolve) => {
            displayResults(data.data, resolve);
          });
        } else {
          throw new Error("Invalid response format: missing output data");
        }
      } catch (itemError) {
        console.error(`Error processing image ${i + 1}:`, itemError);
        throw new Error(
          `Failed to process image ${i + 1}: ${itemError.message}`,
        );
      }
    }
  } catch (error) {
    console.error("Detection error:", error);
    alert("Detection failed: " + error.message);
  } finally {
    hideLoading();
    const loadingText = document.querySelector(".loading-text");
    if (loadingText.getAttribute("data-original")) {
      loadingText.textContent = loadingText.getAttribute("data-original");
    }
    isProcessingQueue = false;
    document.getElementById("runAnalysisBtn").disabled = false;
  }
}
function showLoading() {
  document.getElementById("loadingOverlay").classList.remove("d-none");
}
function hideLoading() {
  document.getElementById("loadingOverlay").classList.add("d-none");
}
function displayResults(data, callback = null) {
  const resultImg = document.getElementById("resultImage");
  const resultContainer = document.getElementById("resultImageContainer");

  // data is already the response data (passed as data.data from runDetection)
  outputImagePath = data.output.image;
  outputJSONPath = data.output.json;

  // Create a new image to preload and verify it loads
  const preloadImg = new Image();

  preloadImg.onload = function () {
    // Image loaded successfully, update the display
    resultImg.src = outputImagePath + "?t=" + new Date().getTime();
    resultImg.classList.remove("d-none");
    document.getElementById("resultEmptyState").style.display = "none";
    resultContainer.classList.remove("loading");

    // Update statistics
    updateStatistics(data);
    enableExportButtons();
    if (callback) callback();
  };

  preloadImg.onerror = function () {
    resultContainer.classList.remove("loading");
    console.error("Failed to load result image from:", outputImagePath);
    alert(
      "Failed to load result image. The detection may have failed. Please try again.",
    );
    if (callback) callback();
  };

  // Start preloading the image
  resultContainer.classList.add("loading");
  preloadImg.src = outputImagePath;
}
function updateStatistics(data) {
  appSessionStats.imagesProcessed += 1;
  appSessionStats.totalDefects += data.statistics.total_detections;

  appSessionStats.confidenceSum += data.statistics.average_confidence;
  appSessionStats.timeSum += data.statistics.inference_time;

  const detections = data.statistics.detections_by_class;
  appSessionStats.categories["D40 - Pothole"] +=
    detections["D40 - Pothole"] || 0;
  appSessionStats.categories["D00 - Longitudinal Crack"] +=
    detections["D00 - Longitudinal Crack"] || 0;
  appSessionStats.categories["D10 - Transverse Crack"] +=
    detections["D10 - Transverse Crack"] || 0;
  appSessionStats.categories["D20 - Alligator Crack"] +=
    detections["D20 - Alligator Crack"] || 0;

  document.getElementById("totalDefects").textContent =
    appSessionStats.totalDefects;

  const avgConf = (
    (appSessionStats.confidenceSum / appSessionStats.imagesProcessed) *
    100
  ).toFixed(1);
  document.getElementById("avgConfidence").textContent = avgConf + "%";

  const time = (
    (appSessionStats.timeSum / appSessionStats.imagesProcessed) *
    1000
  ).toFixed(0);
  document.getElementById("inferenceTime").textContent = time + "ms";

  document.getElementById("countD40").textContent = String(
    appSessionStats.categories["D40 - Pothole"],
  ).padStart(2, "0");
  document.getElementById("countD00").textContent = String(
    appSessionStats.categories["D00 - Longitudinal Crack"],
  ).padStart(2, "0");
  document.getElementById("countD10").textContent = String(
    appSessionStats.categories["D10 - Transverse Crack"],
  ).padStart(2, "0");
  document.getElementById("countD20").textContent = String(
    appSessionStats.categories["D20 - Alligator Crack"],
  ).padStart(2, "0");
}
function enableExportButtons() {
  document.getElementById("btnDownloadImage").disabled = false;
  document.getElementById("btnDownloadJSON").disabled = false;
  document.getElementById("btnViewStats").disabled = false;
}
function disableExportButtons() {
  document.getElementById("btnDownloadImage").disabled = true;
  document.getElementById("btnDownloadJSON").disabled = true;
  document.getElementById("btnViewStats").disabled = true;
}
function downloadImage() {
  if (historyPNGs.length === 0) {
    alert("No result image available");
    return;
  }
  if (historyPNGs.length === 1) {
    const link = document.createElement("a");
    const filename = historyPNGs[0].split("/").pop().split("?")[0];
    link.href = "/download/" + filename;
    link.download = "detection_result.png";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } else {
    handleZipDownload(historyPNGs, "images_results.zip");
  }
}

function downloadJSON() {
  if (historyJSONs.length === 0) {
    alert("No JSON data available");
    return;
  }
  if (historyJSONs.length === 1) {
    const link = document.createElement("a");
    link.href = historyJSONs[0];
    link.download = "detection_data.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } else {
    handleZipDownload(historyJSONs, "data_results.zip");
  }
}

function handleZipDownload(fileUrls, outFilename) {
  const filenames = fileUrls.map((url) => url.split("/").pop().split("?")[0]);
  fetch("/zip_results", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ files: filenames }),
  })
    .then((response) => response.blob())
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = outFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    })
    .catch(console.error);
}

function viewStatistics() {
  if (appSessionStats.imagesProcessed === 0) {
    alert("No statistics available yet");
    return;
  }
  sessionStorage.setItem("appSessionStats", JSON.stringify(appSessionStats));
  window.open("/statistics", "_blank");
}
function zoomIn() {
  zoomLevel = Math.min(zoomLevel + 0.2, 3);
  applyZoom();
}
function zoomOut() {
  zoomLevel = Math.max(zoomLevel - 0.2, 0.5);
  applyZoom();
}
function resetZoom() {
  zoomLevel = 1;
  applyZoom();
}
function applyZoom() {
  const imgs = document.querySelectorAll(".display-image");
  imgs.forEach((img) => {
    img.style.transform = `scale(${zoomLevel})`;
  });
}
function toggleFullscreen() {
  const container = document.querySelector(".main-content");
  if (!document.fullscreenElement) {
    container.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}
function toggleLeftSidebar() {
  const sidebar = document.getElementById("sidebarLeft");
  const mainLayout = document.querySelector(".main-layout");
  sidebar.classList.toggle("collapsed");
  mainLayout.classList.toggle("left-collapsed");
  if (sidebar.classList.contains("collapsed")) {
    localStorage.setItem("leftSidebarCollapsed", "true");
  } else {
    localStorage.removeItem("leftSidebarCollapsed");
  }
}
function toggleRightSidebar() {
  const sidebar = document.getElementById("sidebarRight");
  const mainLayout = document.querySelector(".main-layout");
  sidebar.classList.toggle("collapsed");
  mainLayout.classList.toggle("right-collapsed");
  if (sidebar.classList.contains("collapsed")) {
    localStorage.setItem("rightSidebarCollapsed", "true");
  } else {
    localStorage.removeItem("rightSidebarCollapsed");
  }
}
function initSidebarStates() {
  const mainLayout = document.querySelector(".main-layout");
  if (localStorage.getItem("leftSidebarCollapsed") === "true") {
    document.getElementById("sidebarLeft").classList.add("collapsed");
    if (mainLayout) mainLayout.classList.add("left-collapsed");
  }
  if (localStorage.getItem("rightSidebarCollapsed") === "true") {
    document.getElementById("sidebarRight").classList.add("collapsed");
    if (mainLayout) mainLayout.classList.add("right-collapsed");
  }
}

// Theme Management
function initThemeState() {
  const currentTheme = localStorage.getItem("appTheme") || "light";
  if (currentTheme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    document.getElementById("themeIcon").className = "bi bi-sun";
  }
}

function toggleTheme() {
  const root = document.documentElement;
  const newTheme =
    root.getAttribute("data-theme") === "dark" ? "light" : "dark";

  if (newTheme === "dark") {
    root.setAttribute("data-theme", "dark");
    document.getElementById("themeIcon").className = "bi bi-sun";
  } else {
    root.removeAttribute("data-theme");
    document.getElementById("themeIcon").className = "bi bi-moon-stars";
  }

  localStorage.setItem("appTheme", newTheme);
}
