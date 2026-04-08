const signinForm = document.getElementById('signinForm');
const fullNameInput = document.getElementById('fullName');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const agreeTermsInput = document.getElementById('agreeTerms');
const togglePasswordButton = document.getElementById('togglePassword');
const themeToggle = document.getElementById('themeToggle');
const mathBackground = document.getElementById('mathBackground');
const signinButton = document.getElementById('signinButton');
const statusText = document.getElementById('statusText');

const nameError = document.getElementById('nameError');
const emailError = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');
const confirmPasswordError = document.getElementById('confirmPasswordError');
const termsError = document.getElementById('termsError');

let hasParallaxListener = false;

const AUTH_BASE_URL = 'https://h4t-cipher-1.onrender.com';
const SIGNUP_API_URL = `${AUTH_BASE_URL}/signup`;
const HOME_PAGE_URL = '../homepage/homepage.html';
const TOKEN_KEY = 'token';

/* ------------------ UI + BACKGROUND ------------------ */

function randomInRange(min, max) {
	return Math.random() * (max - min) + min;
}

function createMathNode(index) {
	const element = document.createElement('div');
	element.className = 'math-float';

	const vw = window.innerWidth;
	const vh = window.innerHeight;

	element.style.width = `${randomInRange(110, 230)}px`;
	element.style.height = `${randomInRange(78, 150)}px`;
	element.style.setProperty('--x', `${randomInRange(-0.05 * vw, 0.95 * vw)}px`);
	element.style.setProperty('--y', `${randomInRange(-0.08 * vh, 1.02 * vh)}px`);

	element.dataset.depth = randomInRange(0.2, 1).toFixed(3);

	return element;
}

function initMathBackground() {
	if (!mathBackground) return;

	mathBackground.innerHTML = '';
	for (let i = 0; i < 20; i++) {
		mathBackground.appendChild(createMathNode(i));
	}
}

/* ------------------ VALIDATION ------------------ */

function showFieldError(field, errorElement, message) {
	errorElement.textContent = message;
	field.setAttribute('aria-invalid', 'true');
}

function clearFieldError(field, errorElement) {
	errorElement.textContent = '';
	field.removeAttribute('aria-invalid');
}

function validateEmail(value) {
	return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function validateForm() {
	let isValid = true;

	const fullName = fullNameInput.value.trim();
	const email = emailInput.value.trim();
	const password = passwordInput.value;
	const confirmPassword = confirmPasswordInput.value;

	clearFieldError(fullNameInput, nameError);
	clearFieldError(emailInput, emailError);
	clearFieldError(passwordInput, passwordError);
	clearFieldError(confirmPasswordInput, confirmPasswordError);
	clearFieldError(agreeTermsInput, termsError);

	if (!fullName || fullName.length < 2) {
		showFieldError(fullNameInput, nameError, 'Enter your full name');
		isValid = false;
	}

	if (!email || !validateEmail(email)) {
		showFieldError(emailInput, emailError, 'Enter valid email');
		isValid = false;
	}

	if (!password || password.length < 8) {
		showFieldError(passwordInput, passwordError, 'Min 8 chars');
		isValid = false;
	}

	if (confirmPassword !== password) {
		showFieldError(confirmPasswordInput, confirmPasswordError, 'Passwords mismatch');
		isValid = false;
	}

	if (!agreeTermsInput.checked) {
		showFieldError(agreeTermsInput, termsError, 'Accept terms');
		isValid = false;
	}

	return isValid;
}

function setStatus(message, type) {
	statusText.textContent = message;
	statusText.className = type || '';
}

/* ------------------ EVENTS ------------------ */

togglePasswordButton.addEventListener('click', () => {
	const isHidden = passwordInput.type === 'password';
	passwordInput.type = isHidden ? 'text' : 'password';
	confirmPasswordInput.type = isHidden ? 'text' : 'password';
});

signinForm.addEventListener('submit', async (event) => {
	event.preventDefault();

	if (!validateForm()) {
		setStatus('Fix errors', 'error');
		return;
	}

	signinButton.disabled = true;
	setStatus('Creating account...', '');

	try {
		const response = await fetch(SIGNUP_API_URL, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				email: emailInput.value.trim().toLowerCase(),
				password: passwordInput.value,
				full_name: fullNameInput.value.trim(),
			}),
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.detail || 'Signup failed');
		}

		if (data.access_token) {
			localStorage.setItem(TOKEN_KEY, data.access_token);
		}

		setStatus('Success! Redirecting...', 'success');
		window.location.href = HOME_PAGE_URL;

	} catch (err) {
		setStatus(err.message, 'error');
		signinButton.disabled = false;
	}
});

/* ------------------ INIT ------------------ */

initMathBackground();