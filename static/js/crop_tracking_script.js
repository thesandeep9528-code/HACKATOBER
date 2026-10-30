// Farm Input Variables
const farmSelect = document.getElementById('farmSelect');
const formContainer = document.getElementById('trackingFormContainer');
const farmNameDisplay = document.getElementById('selectedFarmName');
const cropInfoDisplay = document.getElementById('selectedCropInfo');
const activeFarmInput = document.getElementById('activeFarmId');
const weekBadge = document.getElementById('currentWeekBadge');
const establishmentCard = document.getElementById('cardEstablishment');
const submitBtn = document.getElementById('submitLogBtn');
const alertArea = document.getElementById('alertArea');
const stageContainer = document.getElementById("stageContainer");
const lccScoreSelect = document.getElementById("lcc_score");
const height = document.getElementById("height");
const standCount = document.getElementById("stand_count");

// Charts Variables
const logisticsBtn = document.getElementById('showLogisticsBtn');
const heightChartImg = document.getElementById('heightChartImg');
const stageChartImg = document.getElementById('stageChartImg');
const chartsLoader = document.getElementById('chartsLoader');
const chartsContainer = document.getElementById('chartsContainer');

// 1. Handle Farm Selection
farmSelect.addEventListener('change', async function () {
    const selectedOption = this.options[this.selectedIndex];

    if (selectedOption.value) {
        // Get data attributes
        const farmId = selectedOption.value;
        const farmLabel = selectedOption.text.split('(')[0]; // Extract name
        const cropName = selectedOption.getAttribute('data-crop-name');
        const weekNum = parseInt(selectedOption.getAttribute('data-week'));

        // Populate UI
        farmNameDisplay.textContent = farmLabel;
        cropInfoDisplay.textContent = cropName;
        activeFarmInput.value = farmId;
        weekBadge.textContent = `Week ${weekNum}`;

        // Logic: Hide Establishment Card if Week > 4
        if (weekNum > 4) {
            establishmentCard.classList.add('hidden');
        } else {
            establishmentCard.classList.remove('hidden');
        }

        const response = await fetch(`api/crop_standards/${farmId}`);
        const data = await response.json();

        if (data && response.ok) {
            lccScoreSelect.innerHTML = `<option value="" selected>Select Score...</option>
                                    <option value="1">1 - Yellowish Green (Starved)</option>
                                    <option value="2">2 - Pale Green</option>
                                    <option value="3">3 - Green${(data.optimal_lcc == 3) ? ' (Optimal)' : ''}</option>
                                    <option value="4">4 - Dark Green${(data.optimal_lcc == 4) ? ' (Optimal)' : ''}</option>
                                    <option value="5">5 - Very Dark Green${(data.optimal_lcc == 5) ? ' (Optimal)' : ''}</option>
                                    <option value="6">6 - Excessive Nitrogen</option>`

            stageContainer.innerHTML = "";
            let tailwindColors = [
                { text: 'text-emerald-700', bg: 'peer-checked:bg-emerald-50', border: 'peer-checked:border-emerald-500' },
                { text: 'text-amber-700', bg: 'peer-checked:bg-amber-50', border: 'peer-checked:border-amber-500' },
                { text: 'text-blue-700', bg: 'peer-checked:bg-blue-50', border: 'peer-checked:border-blue-500' },
                { text: 'text-purple-700', bg: 'peer-checked:bg-purple-50', border: 'peer-checked:border-purple-500' }
            ];

            data.stages.forEach((stage, index) => {
                let colorClass = tailwindColors[index % tailwindColors.length];

                let wrapper = document.createElement('div');
                wrapper.className = "flex-1 relative";

                let inputField = document.createElement('input');
                inputField.setAttribute('type', 'radio');
                inputField.setAttribute('class', 'hidden peer');
                inputField.setAttribute('name', 'phenology_stage');
                inputField.setAttribute('value', stage[0]);
                inputField.setAttribute('id', `stage_${stage[0]}`);
                inputField.setAttribute('autocomplete', 'off');

                let label = document.createElement('label');
                label.setAttribute('class', `flex items-center justify-center w-full px-4 py-3 border-2 border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50 transition-all font-bold text-sm text-center ${colorClass.text} ${colorClass.border} ${colorClass.bg}`);
                label.setAttribute('for', `stage_${stage[0]}`);
                label.innerText = stage[1].label;

                wrapper.appendChild(inputField);
                wrapper.appendChild(label);
                stageContainer.appendChild(wrapper);
            });

            activeFarmInput.value = farmId;

            // Populate Latest Health Record
            const healthBox = document.getElementById('farmHealthBadgeContainer');
            if (healthBox) {
                if (data.latest_disease) {
                    const isHealthy = data.latest_disease.label.toLowerCase().includes('healthy');
                    const config = isHealthy
                        ? { bg: 'bg-emerald-50', border: 'border-emerald-100', textMain: 'text-emerald-800', badge: 'bg-emerald-600', icon: 'text-emerald-500' }
                        : { bg: 'bg-rose-50', border: 'border-rose-100', textMain: 'text-rose-800', badge: 'bg-rose-600', icon: 'text-rose-500' };

                    healthBox.className = `flex flex-col sm:flex-row justify-between sm:items-center p-5 rounded-2xl border mb-6 shadow-sm ${config.bg} ${config.border}`;
                    healthBox.innerHTML = `
                        <div class="mb-3 sm:mb-0">
                            <strong class="flex items-center gap-2 ${config.textMain} text-sm mb-1">
                                <i data-lucide="stethoscope" class="w-4 h-4 ${config.icon}"></i> Latest Foliage Health Record:
                            </strong>
                            <div class="flex items-center gap-2">
                                <span class="font-bold text-gray-900 text-lg">${data.latest_disease.label}</span>
                                <span class="px-2.5 py-1 ${config.badge} text-white text-[10px] uppercase tracking-wider font-extrabold rounded-md shadow-sm">${data.latest_disease.confidence}% Confidence</span>
                            </div>
                            <span class="text-xs font-semibold text-gray-500 mt-1 block">Logged on ${data.latest_disease.date}</span>
                        </div>
                        <div>
                            <a href="/disease_detection" class="inline-flex items-center gap-2 px-4 py-2 ${config.badge} hover:opacity-90 text-white text-sm font-bold rounded-xl shadow-sm transition-opacity">
                                <i data-lucide="camera" class="w-4 h-4"></i> Rescan Foliage
                            </a>
                        </div>
                    `;
                } else {
                    healthBox.className = 'flex flex-col sm:flex-row justify-between sm:items-center p-5 rounded-2xl border border-gray-200 bg-gray-50 mb-6 shadow-sm';
                    healthBox.innerHTML = `
                        <div class="mb-3 sm:mb-0 flex items-center gap-3">
                            <div class="w-10 h-10 bg-white rounded-full flex items-center justify-center border border-gray-200 shadow-sm">
                                <i data-lucide="leaf" class="w-5 h-5 text-emerald-500"></i>
                            </div>
                            <span class="text-sm font-semibold text-gray-600">No foliage diagnosis logged for this farm yet.</span>
                        </div>
                        <div>
                            <a href="/disease_detection" class="inline-flex items-center gap-2 px-4 py-2 bg-white border-2 border-emerald-500 text-emerald-600 hover:bg-emerald-50 text-sm font-bold rounded-xl shadow-sm transition-colors">
                                <i data-lucide="camera" class="w-4 h-4"></i> Scan Leaf Now
                            </a>
                        </div>
                    `;
                }
            }

            formContainer.classList.remove('hidden');
        }
        else {
            console.log(data.error);
        }
        // Show Option for charts
        logisticsBtn.classList.remove('hidden');
        lucide.createIcons();
    }
});

// 2. Handle Form Submission
submitBtn.addEventListener('click', async function () {
    const moisture = document.querySelector("#moistureBox input:checked");
    const stage = document.querySelector("#stageContainer input:checked");

    const formData = {
        moisture: (moisture) ? moisture.value : null,
        height: height.value,
        lcc: lccScoreSelect.value,
        stage: (stage) ? stage.value : null,
        stand_count: standCount.value
    }

    const farmId = activeFarmInput.value;

    // Reset Alerts
    alertArea.innerHTML = '';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<svg class="animate-spin h-5 w-5 text-white mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Saving...';

    try {
        const response = await fetch(`/log_field_data/${farmId}`, {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="save" class="w-5 h-5 mr-2"></i> Save Field Log';
        lucide.createIcons();

        // Show Alerts (The Roast/Advice)
        if (data.alerts && data.alerts.length > 0) {
            let alertHTML = '';
            data.alerts.forEach(alert => {
                alertHTML += `
                    <div class="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-4 flex gap-3 shadow-sm relative pr-10">
                        <i data-lucide="alert-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-600"></i>
                        <div class="text-sm font-semibold">${alert}</div>
                        <button type="button" class="absolute top-4 right-4 text-amber-700 hover:text-amber-900" onclick="this.parentElement.remove()">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                `;
            });
            alertArea.innerHTML = alertHTML;
            lucide.createIcons();
        } else {
            // Success Message
            alertArea.innerHTML = `
                <div class="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl p-4 flex gap-3 shadow-sm relative pr-10">
                    <i data-lucide="check-circle" class="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600"></i>
                    <div>
                        <strong class="font-bold text-sm block mb-1">Log Saved!</strong>
                        <span class="text-sm font-medium">Great job keeping your records updated.</span>
                    </div>
                    <button type="button" class="absolute top-4 right-4 text-emerald-700 hover:text-emerald-900" onclick="this.parentElement.remove()">
                        <i data-lucide="x" class="w-4 h-4"></i>
                    </button>
                </div>
            `;
            lucide.createIcons();
        }
    }
    catch (error) {
        console.error('Error:', error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="save" class="w-5 h-5 mr-2"></i> Save Field Log';
        alert('An error occurred. Please try again.');
    }
});

logisticsBtn.addEventListener('click', async function () {
    const farmId = activeFarmInput.value;
    if (!farmId) return;

    // Reset Modal State
    chartsLoader.classList.remove('hidden');
    chartsContainer.classList.add('hidden');

    // Fetch Images
    try {
        const response = await fetch(`/api/farm_analytics/${farmId}`)
        const data = await response.json();

        // Inject Base64 Strings
        heightChartImg.src = `data:image/png;base64,${data.height_chart}`;
        stageChartImg.src = `data:image/png;base64,${data.stage_chart}`;

        // Swap Views
        chartsLoader.classList.add('hidden');
        chartsContainer.classList.remove('hidden');
    }
    catch (error) {
        console.error("Chart Error:", error);
        chartsLoader.innerHTML = `<p class="text-red-500 font-bold text-sm">Failed to load charts.</p>`;
    }
});