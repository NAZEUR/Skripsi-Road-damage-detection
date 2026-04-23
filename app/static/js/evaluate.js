let allImages = [];
let selectedImages = new Set();

document.addEventListener("DOMContentLoaded", () => {
    fetchTestImages();
});

function toggleLeftSidebar() {
  const sidebar = document.getElementById("sidebarLeft");
  const mainLayout = document.getElementById("mainLayout");
  const icon = document.getElementById("iconToggleLeft");
  sidebar.classList.toggle("collapsed");
  mainLayout.classList.toggle("left-collapsed");
  if (sidebar.classList.contains("collapsed")) {
    icon.classList.replace("bi-chevron-left", "bi-chevron-right");
  } else {
    icon.classList.replace("bi-chevron-right", "bi-chevron-left");
  }
}

async function fetchTestImages() {
    try {
        const response = await fetch('/api/test_images');
        const data = await response.json();
        
        if (data.success) {
            allImages = data.data;
            filterImages();
        } else {
            console.error("Failed to load test images", data.error);
        }
    } catch (e) {
        console.error(e);
    }
}

function filterImages() {
    const checkboxes = document.querySelectorAll('.country-filter:checked');
    const selectedCountries = Array.from(checkboxes).map(cb => cb.value);
    
    let filtered = allImages.filter(img => {
        return selectedCountries.some(country => img.includes(country));
    });
    
    renderGallery(filtered);
    
    // Update select all state based on filtered visibility
    document.getElementById("selectAllImages").checked = false;
    selectedImages.clear();
    updateSelectedCount();
}

function updateSelectedCount() {
    document.getElementById("selectedCount").textContent = selectedImages.size;
    document.getElementById("btnEvaluateBatch").disabled = selectedImages.size === 0;
}

function toggleSelectAll() {
    const isChecked = document.getElementById("selectAllImages").checked;
    const checkboxes = document.querySelectorAll('.img-select-cb');
    checkboxes.forEach(cb => {
        cb.checked = isChecked;
        if (isChecked) {
            selectedImages.add(cb.value);
        } else {
            selectedImages.delete(cb.value);
        }
    });
    updateSelectedCount();
}

function renderGallery(images) {
    const grid = document.getElementById("imageGrid");
    grid.innerHTML = "";
    
    images.forEach(imgName => {
        const col = document.createElement("div");
        col.className = "col-md-3 col-sm-4 col-6";
        
        const card = document.createElement("div");
        card.className = "card border-0 shadow-sm rounded-4 h-100 image-card";
        card.style.cursor = "pointer";
        card.style.transition = "transform 0.2s";
        card.onmouseover = () => card.style.transform = "scale(1.05)";
        card.onmouseout = () => card.style.transform = "scale(1)";
        
        card.style.position = "relative";
        
        const cbContainer = document.createElement("div");
        cbContainer.className = "position-absolute top-0 start-0 p-2";
        cbContainer.style.zIndex = "10";
        
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "form-check-input img-select-cb shadow-sm";
        cb.style.width = "1.5rem";
        cb.style.height = "1.5rem";
        cb.value = imgName;
        cb.checked = selectedImages.has(imgName);
        cb.onclick = (e) => {
            e.stopPropagation();
            if (cb.checked) {
                selectedImages.add(imgName);
            } else {
                selectedImages.delete(imgName);
                document.getElementById("selectAllImages").checked = false;
            }
            updateSelectedCount();
        };
        cbContainer.appendChild(cb);
        card.appendChild(cbContainer);
        
        card.onclick = () => cb.click();
        
        const img = document.createElement("img");
        img.src = `/api/raw_test_image/${imgName}`;
        img.className = "card-img-top rounded-top-4";
        img.style.height = "150px";
        img.style.objectFit = "cover";
        
        const body = document.createElement("div");
        body.className = "card-body p-2 text-center";
        
        const text = document.createElement("small");
        text.className = "text-muted fw-bold";
        text.style.fontSize = "0.75rem";
        text.textContent = imgName;
        
        body.appendChild(text);
        card.appendChild(img);
        card.appendChild(body);
        col.appendChild(card);
        grid.appendChild(col);
    });
    updateSelectedCount();
}

function showGallery() {
    document.getElementById("evalResultsView").classList.add("d-none");
    document.getElementById("galleryView").classList.remove("d-none");
}

async function evaluateSelected() {
    if (selectedImages.size === 0) return;
    
    document.getElementById("evalLoading").classList.remove("d-none");
    document.getElementById("galleryView").classList.add("d-none");
    
    try {
        const conf = parseFloat(document.getElementById("confidenceSlider").value) / 100;
        const slice_size = parseInt(document.getElementById("sliceSizeSlider").value);
        const overlap = parseFloat(document.getElementById("overlapSlider").value);
        const match = parseFloat(document.getElementById("matchSlider").value);
        
        const payload = {
            filenames: Array.from(selectedImages),
            confidence: conf,
            slice_height: slice_size,
            slice_width: slice_size,
            overlap_ratio: overlap,
            match_threshold: match
        };
        
        const response = await fetch('/api/evaluate_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderBatchResults(data.data);
        } else {
            alert("Batch evaluation failed: " + data.error);
            showGallery();
        }
    } catch (e) {
        console.error(e);
        alert("Batch evaluation failed: " + e.message);
        showGallery();
    } finally {
        document.getElementById("evalLoading").classList.add("d-none");
    }
}

function renderBatchResults(data) {
    document.getElementById("evalResultsView").classList.remove("d-none");
    document.getElementById("evalTitle").textContent = `Batch Evaluation Results (${data.images.length} Images)`;
    
    const container = document.getElementById("batchResultsContainer");
    container.innerHTML = "";
    
    const t = new Date().getTime();
    
    data.images.forEach((imgData, index) => {
        const row = document.createElement("div");
        row.className = "col-12 mb-4";
        row.innerHTML = `
            <div class="card border-0 shadow-sm rounded-4">
                <div class="card-header bg-light border-0 py-3 d-flex justify-content-between align-items-center">
                    <h5 class="mb-0 fw-bold text-primary">#${index + 1}: ${imgData.filename}</h5>
                </div>
                <div class="card-body p-4">
                    <div class="row g-4">
                        <div class="col-md-6 text-center">
                            <h6 class="fw-bold mb-3 text-secondary">GT vs YOLOv11 (Baseline)</h6>
                            <img src="${imgData.baseline_image}?t=${t}" class="img-fluid rounded shadow-sm w-100" style="object-fit: contain; max-height: 400px; background: #000;">
                        </div>
                        <div class="col-md-6 text-center">
                            <h6 class="fw-bold mb-3 text-secondary">GT vs SAHI</h6>
                            <img src="${imgData.sahi_image}?t=${t}" class="img-fluid rounded shadow-sm w-100" style="object-fit: contain; max-height: 400px; background: #000;">
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(row);
    });
    
    const tbody = document.getElementById("metricsTableBody");
    tbody.innerHTML = `
        <tr>
            <td class="text-start fw-bold" style="color: var(--primary);">YOLOv11 (Baseline)</td>
            <td>${data.baseline_metrics.Precision}</td>
            <td>${data.baseline_metrics.Recall}</td>
            <td>${data.baseline_metrics['F1-Score']}</td>
            <td>${data.baseline_metrics['mAP@50']}</td>
            <td>${data.baseline_metrics['mAP@50-95']}</td>
            <td style="color: var(--warning); font-weight: bold;">${data.baseline_metrics['Eval Time']}</td>
        </tr>
        <tr>
            <td class="text-start fw-bold" style="color: var(--primary);">SAHI (Sliced)</td>
            <td>${data.sahi_metrics.Precision}</td>
            <td>${data.sahi_metrics.Recall}</td>
            <td>${data.sahi_metrics['F1-Score']}</td>
            <td>${data.sahi_metrics['mAP@50']}</td>
            <td>${data.sahi_metrics['mAP@50-95']}</td>
            <td style="color: var(--warning); font-weight: bold;">${data.sahi_metrics['Eval Time']}</td>
        </tr>
    `;
}
