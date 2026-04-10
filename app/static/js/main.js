// Road Damage Detection - Complete JavaScript
let uploadedFilePath = null,
  uploadedFileName = null,
  outputImagePath = null,
  outputJSONPath = null,
  appConfig = null,
  zoomLevel = 1;
document.addEventListener("DOMContentLoaded", initApp);
async function initApp() {
  try {
    await loadConfig();
    await checkHealth();
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
async function checkHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    const gpuStatus = document.getElementById("gpuStatus");
    if (data.success && data.data.models.device === "cuda") {
      gpuStatus.innerHTML = "GPU: <strong>Active</strong>";
    } else {
      gpuStatus.innerHTML = "GPU: <strong>CPU Mode</strong>";
    }
  } catch (error) {
    document.getElementById("gpuStatus").innerHTML =
      "GPU: <strong>Offline</strong>";
  }
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
      uploadedFilePath = data.data.filepath;
      uploadedFileName = data.data.filename;
      showImagePreview(file, data.data);
      document.getElementById("runAnalysisBtn").disabled = false;
    } else {
      alert("Upload failed: " + data.error);
    }
  } catch (error) {
    console.error("Upload error:", error);
    alert("Upload failed: " + error.message);
  }
}
function validateFile(file) {
  const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/bmp"];
  if (!allowedTypes.includes(file.type)) {
    alert("Invalid file type. Please upload JPG, PNG, or BMP");
    return false;
  }
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    alert("File too large. Maximum 10MB");
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
  document.getElementById("fileInput").value = "";
  document.getElementById("originalImage").classList.add("d-none");
  document.getElementById("resultImage").classList.add("d-none");
  document.getElementById("emptyState").style.display = "block";
  document.getElementById("resultEmptyState").style.display = "block";
  document.getElementById("fileInfo").classList.add("d-none");
  document.getElementById("runAnalysisBtn").disabled = true;
  resetStatistics();
  disableExportButtons();
}
async function runDetection() {
  if (!uploadedFilePath) {
    alert("Please upload an image first");
    return;
  }
  try {
    const mode = document.querySelector(
      'input[name="detectionMode"]:checked',
    ).value;
    const confidence =
      parseFloat(document.getElementById("confidenceSlider").value) / 100;
    const params = {
      filepath: uploadedFilePath,
      mode: mode,
      confidence: confidence,
    };
    if (mode === "sahi") {
      params.slice_height = parseInt(
        document.getElementById("sliceSizeSlider").value,
      );
      params.slice_width = parseInt(
        document.getElementById("sliceSizeSlider").value,
      );
      params.overlap_ratio = parseFloat(
        document.getElementById("overlapSlider").value,
      );
      params.match_threshold = parseFloat(
        document.getElementById("matchSlider").value,
      );
    }
    showLoading();
    const response = await fetch("/detect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    const data = await response.json();
    if (data.success) {
      outputImagePath = data.data.output.image;
      outputJSONPath = data.data.output.json;
      displayResults(data.data);
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error("Detection error:", error);
    alert("Detection failed: " + error.message);
  } finally {
    hideLoading();
  }
}
function showLoading() {
  document.getElementById("loadingOverlay").classList.remove("d-none");
}
function hideLoading() {
  document.getElementById("loadingOverlay").classList.add("d-none");
}
function displayResults(data) {
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
  };

  preloadImg.onerror = function () {
    resultContainer.classList.remove("loading");
    console.error("Failed to load result image from:", outputImagePath);
    alert(
      "Failed to load result image. The detection may have failed. Please try again.",
    );
  };

  // Start preloading the image
  resultContainer.classList.add("loading");
  preloadImg.src = outputImagePath;
}
function updateStatistics(data) {
  document.getElementById("totalDefects").textContent =
    data.statistics.total_detections;
  const avgConf = (data.statistics.average_confidence * 100).toFixed(1);
  document.getElementById("avgConfidence").textContent = avgConf + "%";
  const time = (data.statistics.inference_time * 1000).toFixed(0);
  document.getElementById("inferenceTime").textContent = time + "ms";
  const detections = data.statistics.detections_by_class;
  document.getElementById("countD40").textContent = String(
    detections["D40 - Pothole"] || 0,
  ).padStart(2, "0");
  document.getElementById("countD00").textContent = String(
    detections["D00 - Longitudinal Crack"] || 0,
  ).padStart(2, "0");
  document.getElementById("countD10").textContent = String(
    detections["D10 - Transverse Crack"] || 0,
  ).padStart(2, "0");
  document.getElementById("countD20").textContent = String(
    detections["D20 - Alligator Crack"] || 0,
  ).padStart(2, "0");
}
function resetStatistics() {
  document.getElementById("totalDefects").textContent = "0";
  document.getElementById("avgConfidence").textContent = "0%";
  document.getElementById("inferenceTime").textContent = "0ms";
  document.getElementById("countD40").textContent = "00";
  document.getElementById("countD00").textContent = "00";
  document.getElementById("countD10").textContent = "00";
  document.getElementById("countD20").textContent = "00";
}
function enableExportButtons() {
  document.getElementById("btnDownloadResults").disabled = false;
  document.getElementById("btnViewStats").disabled = false;
}
function disableExportButtons() {
  document.getElementById("btnDownloadResults").disabled = true;
  document.getElementById("btnViewStats").disabled = true;
}
function downloadImage() {
  if (!outputImagePath) {
    alert("No result image available");
    return;
  }
  const link = document.createElement("a");
  // outputImagePath is now a full URL like /view/filename
  // We need to extract the filename and download it
  const filename = outputImagePath.split("/").pop().split("?")[0];
  link.href = "/download/" + filename;
  link.download = "detection_result.png";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
function downloadJSON() {
  if (!outputJSONPath) {
    alert("No JSON data available");
    return;
  }
  const link = document.createElement("a");
  // outputJSONPath is already a full URL like /download/filename
  link.href = outputJSONPath;
  link.download = "detection_data.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
function viewStatistics() {
  if (!outputJSONPath) {
    alert("No statistics available");
    return;
  }
  const modal = new bootstrap.Modal(document.getElementById("statsModal"));
  modal.show();
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
  if (sidebar.classList.contains("collapsed")) {
    localStorage.setItem("rightSidebarCollapsed", "true");
  } else {
    localStorage.removeItem("rightSidebarCollapsed");
  }
}
function initSidebarStates() {
  if (localStorage.getItem("leftSidebarCollapsed") === "true") {
    document.getElementById("sidebarLeft").classList.add("collapsed");
  }
  if (localStorage.getItem("rightSidebarCollapsed") === "true") {
    document.getElementById("sidebarRight").classList.add("collapsed");
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
  const newTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  
  if (newTheme === "dark") {
    root.setAttribute("data-theme", "dark");
    document.getElementById("themeIcon").className = "bi bi-sun";
  } else {
    root.removeAttribute("data-theme");
    document.getElementById("themeIcon").className = "bi bi-moon-stars";
  }
  
  localStorage.setItem("appTheme", newTheme);
}
