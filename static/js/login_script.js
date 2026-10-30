// Safety check to see if lucide cdn is actually loaded
if (window.lucide) {
    lucide.createIcons();
}

const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");
const formLogin = document.getElementById("form-login");
const formRegister = document.getElementById("form-register");

tabRegister.addEventListener("click", () => {
    tabRegister.classList.add("bg-white", "shadow-sm", "text-gray-900");
    tabRegister.classList.remove("text-gray-500");
    tabLogin.classList.remove("bg-white", "shadow-sm", "text-gray-900");
    tabLogin.classList.add("text-gray-500");

    formLogin.classList.add("hidden");
    formRegister.classList.remove("hidden");

    if (window.lucide) lucide.createIcons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

tabLogin.addEventListener("click", () => {
    tabLogin.classList.add("bg-white", "shadow-sm", "text-gray-900");
    tabLogin.classList.remove("text-gray-500");
    tabRegister.classList.remove("bg-white", "shadow-sm", "text-gray-900");
    tabRegister.classList.add("text-gray-500");

    formRegister.classList.add("hidden");
    formLogin.classList.remove("hidden");

    if (window.lucide) lucide.createIcons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});


const regFullname = document.getElementById("reg-fullname");
const errFullname = document.getElementById("err-fullname");

const regEmail = document.getElementById("reg-email");
const errEmail = document.getElementById("err-email");

const regPassword = document.getElementById("reg-password");
const errPassword = document.getElementById("err-password");

const regConfirm = document.getElementById("reg-confirm");
const errConfirm = document.getElementById("err-confirm");

const regLocation = document.getElementById("reg-location");
const errLocation = document.getElementById("err-location");

const regDob = document.getElementById("reg-dob");
const errDob = document.getElementById("err-dob");

const regMobile = document.getElementById("reg-mobile");
const errMobile = document.getElementById("err-mobile");

const registerBtn = document.getElementById("registerBtn");

const loginPassword = document.getElementById("login-password");

const toggleLoginPasswordBtn = document.getElementById("toggleLoginPasswordBtn");
const toggleRegPasswordBtn = document.getElementById("toggleRegPasswordBtn");
const toggleConfirmPasswordBtn = document.getElementById("toggleConfirmPasswordBtn");

// Show password buttons event listeners
toggleLoginPasswordBtn.addEventListener("click", () => { togglePassword(loginPassword, toggleLoginPasswordBtn); });
toggleRegPasswordBtn.addEventListener("click", () => { togglePassword(regPassword, toggleRegPasswordBtn); });
toggleConfirmPasswordBtn.addEventListener("click", () => { togglePassword(regConfirm, toggleConfirmPasswordBtn); });

// Reusable function for show Password functionality in 3 password fields
function togglePassword(passwordField, buttonElement) {
    const isPassword = passwordField.type === "password";
    passwordField.type = (isPassword) ? "text" : "password";

    buttonElement.innerHTML = (isPassword) ? `<i data-lucide="eye-off" class="w-5 h-5"></i>` : `<i data-lucide="eye" class="w-5 h-5"></i>`;
    lucide.createIcons();
}

function validateFullname() {
    if (regFullname.value === "") {
        errFullname.classList.add("hidden");
        return false;
    }

    if (regFullname.value.trim().length < 3) {
        errFullname.classList.remove("hidden");
        return false;
    }
    errFullname.classList.add("hidden");
    return true;
}

const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
function validateEmail() {
    const email = regEmail.value.trim();

    if (email === "") {
        errPassword.classList.add("hidden");
        return false;
    }

    if (!emailRegex.test(email)) {
        errEmail.classList.remove("hidden");
        return false;
    }

    errEmail.classList.add("hidden");
    return true;
}

const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&.]{6,}$/;
function validatePassword() {
    const pwd = regPassword.value;

    if (pwd === "") {
        errPassword.classList.add("hidden");
        return false;
    }

    if (!passwordRegex.test(pwd)) {
        errPassword.classList.remove("hidden");
        return false;
    }

    errPassword.classList.add("hidden");
    return true;
}

function validateConfirmPassword() {
    if (regConfirm.value === "") {
        errConfirm.classList.add("hidden");
        return false;
    }

    if (regConfirm.value !== regPassword.value) {
        errConfirm.classList.remove("hidden");
        return false;
    }

    errConfirm.classList.add("hidden");
    return true;
}

function validateLocation() {
    if (regLocation.value === "") {
        errLocation.classList.add("hidden");
        return false;
    }

    // Split and clean
    const parts = regLocation.value.split(",").map(part => part.trim());

    // Ensure exactly 2 parts AND both parts have text => District, State
    if (parts.length != 2 || parts[0] === "" || parts[1] === "") {
        errLocation.classList.remove("hidden");
        return false;
    }

    errLocation.classList.add("hidden");
    return true;
}

function validateDOB() {
    if (!regDob.value) {
        errDob.classList.add("hidden");
        return false;
    }

    const dob = new Date(regDob.value);
    const today = new Date();

    if (dob > today) {
        errDob.classList.remove("hidden");
        errDob.innerText = "Date of birth cannot be in future";
        return false;
    }

    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();

    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
        age--;
    }

    if (age < 13) {
        errDob.classList.remove("hidden");
        errDob.innerText = "You must be at least 13 years old";
        return false;
    }

    errDob.classList.add("hidden");
    return true;
}

function validateMobile() {
    const mobile = regMobile.value.trim();

    if (mobile === "") {
        errMobile.classList.add("hidden");
        return false;
    }

    if (!/^[6-9]\d{9}$/.test(mobile)) {
        errMobile.classList.remove("hidden");
        return false;
    }

    errMobile.classList.add("hidden");
    return true;
}

function checkRegisterForm() {
    if (
        validateFullname() &&
        validateEmail() &&
        validatePassword() &&
        validateConfirmPassword() &&
        validateLocation() &&
        validateDOB() &&
        validateMobile()
    ) {
        registerBtn.disabled = false;
    } else {
        registerBtn.disabled = true;
    }
}