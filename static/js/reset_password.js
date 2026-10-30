const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");
const errPassword = document.getElementById("errPassword");
const errConfirm = document.getElementById("errConfirm");
const resetBtn = document.getElementById("resetBtn");

// At least 1 letter
// At least 1 number
// minimum 6 characters
const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d).{6,}$/;

function validatePassword() {
    const pwd = newPassword.value.trim();

    if (pwd === "") {
        errPassword.classList.add("d-none");
        return false;
    }

    if (!passwordRegex.test(pwd)) {
        errPassword.classList.remove("d-none");
        return false;
    }

    errPassword.classList.add("d-none");
    return true;
}

function validateConfirmPassword() {
    const confirmPwd = confirmPassword.value.trim();

    if (confirmPwd === "") {
        errConfirm.classList.add("d-none");
        return false;
    }

    if (confirmPwd !== newPassword.value.trim()) {
        errConfirm.classList.remove("d-none");
        return false;
    }

    errConfirm.classList.add("d-none");
    return true;
}

function checkRegisterForm() {
    if (validatePassword() && validateConfirmPassword()) {
        resetBtn.disabled = false;
    } else {
        resetBtn.disabled = true;
    }
}
