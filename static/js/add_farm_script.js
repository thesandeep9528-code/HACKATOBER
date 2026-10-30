lucide.createIcons();

// Simple Client-Side Validation for Date
const dateInput = document.getElementById('sowingDate');
const dateError = document.getElementById('dateError');
const submitBtn = document.getElementById('submitBtn');
const areaAcres = document.getElementById('areaAcres');
const areaError = document.getElementById('areaError');
const farmName = document.getElementById('farmName');
const farmNameError = document.getElementById('farmNameError');
const cropVariety = document.getElementById('cropVariety');
const cropVarietyError = document.getElementById('cropVarietyError');

// Set Max Date to Today (Prevent Future Farming)
// toISOString() gives date string in format "2025-10-02T08:00:00.000Z"
const today = new Date().toISOString().split("T")[0];
dateInput.setAttribute("max", today);

submitBtn.addEventListener('click', event => {
    if (!farmName.value) {
        farmNameError.innerText = "Farm Name is necessary!";
        event.preventDefault();
    }
    if (!areaAcres.value) {
        areaError.innerText = "Area field is necessary!";
        event.preventDefault();
    }
    if (!cropVariety.value) {
        cropVarietyError.innerText = "Crop Variety is necessary!";
        event.preventDefault();
    }
    if (!dateInput.value) {
        dateError.innerText = "Sowing Date cannot be empty!";
        event.preventDefault();
    }
    if (dateInput.value>today) {
        dateError.innerText = "Sowing Date cannot be a future Date!";
        event.preventDefault();
    }
});