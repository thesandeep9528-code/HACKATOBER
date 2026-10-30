lucide.createIcons();

const validSoilTypes = [
    "Alluvial Soil",
    "Black Cotton Soil",
    "Black Soil",
    "Brown Loamy Soil",
    "Clay Loamy Soil",
    "Clay Soil",
    "Cotton Soil",
    "Deep Soil",
    "Friable Soil",
    "Heavy Black Soil",
    "Heavy Soil",
    "Laterite Soil",
    "Light Loamy Soil",
    "Light Soil",
    "Loamy Soil",
    "Medium Black Soil",
    "Red Lateritic Loamy Soil",
    "Red Loamy Soil",
    "Red Soil",
    "Rich Red Loamy Soil",
    "Salty Clay Loamy Soil",
    "Sandy Clay Loamy Soil",
    "Sandy Loamy Soil",
    "Sandy Soil",
    "Shallow Black Soil",
    "Silty Loamy Soil",
    "Well-Drained Loamy Soil",
    "Well-Drained Soil",
    "Well-Grained Deep Loamy Moist Soil"
];

const n = document.getElementById("nitrogen");
const nitrogenError = document.getElementById("nitrogenError");

const p = document.getElementById("phosphorus");
const phosphorusError = document.getElementById("phosphorusError");

const k = document.getElementById("potassium");
const potassiumError = document.getElementById("potassiumError");

const ph = document.getElementById("ph");
const phError = document.getElementById("phError");

const humidity = document.getElementById("humidity");
const humidityError = document.getElementById("humidityError");

const temp = document.getElementById("temperature");
const tempError = document.getElementById("tempError");

const downloadPdfBtn = document.getElementById("downloadPdfBtn");

const soil = document.getElementById("soil");
const soilError = document.getElementById("soilError");
for (let soilType of validSoilTypes) {
    soil.innerHTML += `<option value='${soilType}'>${soilType}</option>`;
}

n.addEventListener("change", event => {
    validateData(n, nitrogenError, "Nitrogen", 0, 300);
});

p.addEventListener("change", event => {
    validateData(p, phosphorusError, "Phosphorus", 0, 300);
});

k.addEventListener("change", event => {
    validateData(k, potassiumError, "Potassium", 0, 300);
});

ph.addEventListener("change", event => {
    validateData(ph, phError, "pH", 0, 14);
});

humidity.addEventListener("change", event => {
    validateData(humidity, humidityError, "Humidity", 0, 100);
});

temp.addEventListener("change", event => {
    validateData(temp, tempError, "Temperature", 0, 60);
});

function validateData(field, errorField, featureName, lowerLimit, upperLimit) {
    if (field.value<lowerLimit || field.value>upperLimit) {
        errorField.innerHTML = `<p class='text-xs font-bold text-red-500 mt-1'>${featureName} value should be between ${lowerLimit} and ${upperLimit}!</p>`;
    }
    else {
        errorField.innerHTML = ``;
    }
}

async function predictCrop(event) {
    event.preventDefault();

    if (soil.value=="==Choose Soil Type==") {
        soilError.innerHTML = `<p class='text-xs font-bold text-red-500 mt-1'>Soil type is necessary!</p>`;
        return;
    }

    // ----- SHOW LOADING -----
    document.getElementById("result-before").classList.add("hidden");
    document.getElementById("result-after").classList.add("hidden");
    document.getElementById("result-loading").classList.remove("hidden");

    // Disable submit button
    const submitBtn = event.target.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.innerText = "Processing...";

    const formData = {
        n: n.value,
        p: p.value,
        k: k.value,
        ph: ph.value,
        temp: temp.value,
        humidity: humidity.value,
        soil_type: soil.value
    }

    const response = await fetch("/api/predict-crop", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(formData)
    });

    const data = await response.json();
    if (!response.ok || data.error) {
        document.getElementById("result-loading").classList.add("hidden");
        document.getElementById("result-before").classList.remove("hidden");
        document.getElementById("result-after").classList.add("hidden");
        document.getElementById("errorMessage").innerText = data.error || "Unknown Error Occured";

        submitBtn.disabled = false;
        submitBtn.innerText = "🌾 Get Recommendation"
    }
    else {
        document.getElementById("cropName").innerText = data.result;
        document.getElementById("matchText").innerText = `${data.match_percentage}% Match`;
        document.getElementById("matchBar").style.width = `${data.match_percentage}%`;
        document.getElementById("harvestTime").innerText = `${data.duration[0]} - ${data.duration[1]}`;
        document.getElementById("waterReqText").innerText = `${data.water_req} mm`;
        downloadPdfBtn.setAttribute("data-report-id", data.report_id);

        const fertList = document.getElementById("fertilizerList");
        if (fertList) {
            fertList.innerHTML = ""; // Clear old recommendations

            data.recommendations.forEach(rec => {
                const li = document.createElement("li");
                li.innerText = rec;
                li.classList.add("flex", "justify-between", "items-center", "p-4", "border-b", "border-gray-100", "last:border-0", "text-sm", "font-medium", "text-gray-700");

                // We convert text to lowercase to safely check keywords
                const lowerRec = rec.toLowerCase();
                if (lowerRec.includes("optimal")) {
                    // Green for good news
                    li.classList.add("bg-emerald-50/50");
                    li.innerHTML += ' <span class="px-2.5 py-1 text-xs font-bold text-emerald-800 bg-emerald-200 rounded-full shadow-sm">✔ Good</span>';
                }
                else if (lowerRec.includes("low")) {
                    // Red for "Action Required" (Low nutrients)
                    li.classList.add("bg-red-50");
                    li.innerHTML += ' <span class="px-2.5 py-1 text-xs font-bold text-red-800 bg-red-200 rounded-full shadow-sm">⚠ Low</span>';
                }
                else if (lowerRec.includes("high")) {
                    // Yellow for "Warning" (High nutrients)
                    li.classList.add("bg-amber-50");
                    li.innerHTML += ' <span class="px-2.5 py-1 text-xs font-bold text-amber-900 bg-amber-300 rounded-full shadow-sm">! High</span>';
                }

                fertList.appendChild(li);
            });
        }

        document.getElementById("result-loading").classList.add("hidden");
        document.getElementById("result-after").classList.remove("hidden");

        submitBtn.disabled = false;
        submitBtn.innerText = "🌾 Get Recommendation";
    }
    lucide.createIcons();
}

downloadPdfBtn.addEventListener("click", async function(event) {
    const reportId = downloadPdfBtn.getAttribute("data-report-id");
    if (!reportId) return alert("Please generate a prediction first!");

    const originalHtml = downloadPdfBtn.innerHTML;
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.innerHTML = `<i class="fa fa-spinner fa-spin me-1"></i> Downloading PDF...`;

    try {
        const response = await fetch(`/download_report/${reportId}`);
        if (!response.ok) throw new Error("Failed to download PDF report.");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;

        let filename = `BioGrow_Crop_Report_${reportId}.pdf`;
        const disposition = response.headers.get("Content-Disposition");
        if (disposition && disposition.indexOf("filename=") !== -1) {
            const matches = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (matches && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (err) {
        alert("Error downloading report: " + err.message);
    } finally {
        downloadPdfBtn.disabled = false;
        downloadPdfBtn.innerHTML = originalHtml;
        if (window.lucide) lucide.createIcons();
    }
});

const addFarmBtn = document.getElementById("addFarmFromPredBtn");
if (addFarmBtn) {
    addFarmBtn.addEventListener("click", async function() {
        const cropName = document.getElementById("cropName").innerText.trim();
        const feedback = document.getElementById("addFarmFeedback");
        if (!cropName) {
            alert("No crop recommendation available to save.");
            return;
        }

        addFarmBtn.disabled = true;
        addFarmBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding to Farm Hub...';

        try {
            const res = await fetch('/api/create_farm_from_prediction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ crop_name: cropName })
            });
            const data = await res.json();
            if (data.error) {
                feedback.className = "text-xs text-center text-red-500 font-bold mt-2";
                feedback.textContent = data.error;
            } else {
                feedback.className = "text-xs text-center text-emerald-600 font-bold mt-2";
                feedback.innerHTML = `<i class="fa fa-check-circle me-1"></i> ${data.message} <a href="${data.redirect_url}" class="underline ms-1 hover:text-emerald-800 transition-colors">View in Crop Tracking →</a>`;
            }
        } catch (err) {
            feedback.className = "text-xs text-center text-red-500 font-bold mt-2";
            feedback.textContent = "Failed to add farm: " + err.message;
        } finally {
            addFarmBtn.disabled = false;
            addFarmBtn.innerHTML = '<i class="fa fa-plus-circle"></i> Add to My Farms & Start Tracking';
        }
    });
}