let allImages = [];

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
        
        card.onclick = () => runEvaluation(imgName);
        
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
}

function showGallery() {
    document.getElementById("evalResultsView").classList.add("d-none");
    document.getElementById("galleryView").classList.remove("d-none");
}

async function runEvaluation(filename) {
    document.getElementById("evalLoading").classList.remove("d-none");
    document.getElementById("galleryView").classList.add("d-none");
    
    try {
        const conf = parseFloat(document.getElementById("confidenceSlider").value) / 100;
        const slice_size = parseInt(document.getElementById("sliceSizeSlider").value);
        const overlap = parseFloat(document.getElementById("overlapSlider").value);
        const match = parseFloat(document.getElementById("matchSlider").value);
        
        const payload = {
            filename: filename,
            confidence: conf,
            slice_height: slice_size,
            slice_width: slice_size,
            overlap_ratio: overlap,
            match_threshold: match
        };
        
        const response = await fetch('/api/evaluate_single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderResults(filename, data.data);
        } else {
            alert("Evaluation failed: " + data.error);
            showGallery();
        }
    } catch (e) {
        console.error(e);
        alert("Evaluation failed: " + e.message);
        showGallery();
    } finally {
        document.getElementById("evalLoading").classList.add("d-none");
    }
}

function renderResults(filename, data) {
    document.getElementById("evalResultsView").classList.remove("d-none");
    document.getElementById("evalTitle").textContent = `Evaluation Results: ${filename}`;
    
    const t = new Date().getTime();
    document.getElementById("imgOriginal").src = data.original;
    document.getElementById("imgGT").src = `${data.gt_image}?t=${t}`;
    document.getElementById("imgBaseline").src = `${data.baseline_image}?t=${t}`;
    document.getElementById("imgSahi").src = `${data.sahi_image}?t=${t}`;
    
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
