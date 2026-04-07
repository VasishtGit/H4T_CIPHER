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

const AUTH_BASE_URL = 'http://localhost:8002';
const SIGNUP_API_URL = `${AUTH_BASE_URL}/signup`;
const LOGIN_PAGE_URL = '../login/login.html';

const mathSvgTemplates = [
	`<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<g class="math-a">
			<line x1="0" y1="20" x2="220" y2="20"></line>
			<line x1="0" y1="55" x2="220" y2="55"></line>
			<line x1="0" y1="90" x2="220" y2="90"></line>
			<line x1="40" y1="0" x2="40" y2="140"></line>
			<line x1="110" y1="0" x2="110" y2="140"></line>
			<line x1="180" y1="0" x2="180" y2="140"></line>
		</g>
		<path class="math-b" d="M0 110 C45 20, 95 120, 140 60 S210 25, 220 86"></path>
	</svg>`,
	`<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<line class="math-c" x1="16" y1="120" x2="206" y2="120"></line>
		<line class="math-c" x1="26" y1="10" x2="26" y2="130"></line>
		<path class="math-a" d="M28 120 Q95 14 188 120"></path>
		<circle class="math-b" cx="126" cy="54" r="4"></circle>
	</svg>`,
	`<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<line class="math-a" x1="12" y1="118" x2="208" y2="118"></line>
		<line class="math-a" x1="40" y1="12" x2="40" y2="128"></line>
		<path class="math-b" d="M0 64 C28 22, 54 22, 82 64 S136 106, 164 64 S192 22, 220 64"></path>
	</svg>`,
	`<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<polyline class="math-c" points="8,118 52,78 92,96 124,46 160,64 208,28"></polyline>
		<line class="math-a" x1="8" y1="118" x2="208" y2="118"></line>
		<line class="math-a" x1="8" y1="18" x2="8" y2="118"></line>
	</svg>`,
];

function randomInRange(min, max) {
	return Math.random() * (max - min) + min;
}

function createMathNode(index) {
	const element = document.createElement('div');
	element.className = 'math-float';

	const vw = window.innerWidth;
	const vh = window.innerHeight;
	const width = randomInRange(110, 230);
	const height = randomInRange(78, 150);
	const x = randomInRange(-0.05 * vw, 0.95 * vw);
	const y = randomInRange(-0.08 * vh, 1.02 * vh);

	element.style.width = `${width}px`;
	element.style.height = `${height}px`;
	element.style.setProperty('--x', `${x}px`);
	element.style.setProperty('--y', `${y}px`);
	element.style.setProperty('--r', `${randomInRange(-12, 12)}deg`);
	element.style.setProperty('--rr', `${randomInRange(-8, 8)}deg`);
	element.style.setProperty('--mx', `${randomInRange(-90, 90)}px`);
	element.style.setProperty('--my', `${randomInRange(-70, 70)}px`);
	element.style.setProperty('--dur', `${randomInRange(18, 38)}s`);
	element.style.setProperty('--delay', `${randomInRange(-24, 0)}s`);
	element.style.setProperty('--alpha', `${randomInRange(0.3, 0.52).toFixed(3)}`);
	element.style.setProperty('--blur', `${randomInRange(0, 0.45).toFixed(2)}px`);
	element.dataset.depth = randomInRange(0.2, 1).toFixed(3);
	element.innerHTML = mathSvgTemplates[index % mathSvgTemplates.length];

	return element;
}

function applyMathParallax(event) {
	if (!mathBackground) {
		return;
	}

	const offsetX = event.clientX / window.innerWidth - 0.5;
	const offsetY = event.clientY / window.innerHeight - 0.5;
	const nodes = mathBackground.querySelectorAll('.math-float');

	nodes.forEach((node) => {
		const depth = Number(node.dataset.depth || 0.4);
		node.style.setProperty('--px', `${(-offsetX * depth * 24).toFixed(2)}px`);
		node.style.setProperty('--py', `${(-offsetY * depth * 18).toFixed(2)}px`);
	});
}

function initMathBackground() {
	if (!mathBackground) {
		return;
	}

	const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	const count = window.innerWidth < 700 ? 16 : window.innerWidth < 1100 ? 24 : 32;
	mathBackground.innerHTML = '';

	for (let index = 0; index < count; index += 1) {
		mathBackground.appendChild(createMathNode(index));
	}

	if (!prefersReducedMotion && !hasParallaxListener) {
		window.addEventListener('mousemove', applyMathParallax, { passive: true });
		hasParallaxListener = true;
	}
}

function updateThemeToggle() {
	const isLight = document.body.classList.contains('light-theme');
	themeToggle.textContent = isLight ? '☀️' : '🌙';
	themeToggle.setAttribute('aria-label', isLight ? 'Switch to dark theme' : 'Switch to light theme');
}

function applySavedTheme() {
	const savedTheme = localStorage.getItem('theme');
	if (savedTheme === 'light') {
		document.body.classList.add('light-theme');
	} else {
		document.body.classList.remove('light-theme');
	}
	updateThemeToggle();
}

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
		showFieldError(fullNameInput, nameError, 'Please enter your full name.');
		isValid = false;
	}

	if (!email) {
		showFieldError(emailInput, emailError, 'Please enter your email address.');
		isValid = false;
	} else if (!validateEmail(email)) {
		showFieldError(emailInput, emailError, 'Please enter a valid email address.');
		isValid = false;
	}

	if (!password) {
		showFieldError(passwordInput, passwordError, 'Please create a password.');
		isValid = false;
	} else if (password.length < 8) {
		showFieldError(passwordInput, passwordError, 'Password must be at least 8 characters long.');
		isValid = false;
	}

	if (!confirmPassword) {
		showFieldError(confirmPasswordInput, confirmPasswordError, 'Please confirm your password.');
		isValid = false;
	} else if (confirmPassword !== password) {
		showFieldError(confirmPasswordInput, confirmPasswordError, 'Passwords do not match.');
		isValid = false;
	}

	if (!agreeTermsInput.checked) {
		showFieldError(agreeTermsInput, termsError, 'Please accept the terms to continue.');
		isValid = false;
	}

	return isValid;
}

function setStatus(message, type) {
	statusText.textContent = message;
	statusText.classList.remove('success', 'error');
	if (type) {
		statusText.classList.add(type);
	}
}

togglePasswordButton.addEventListener('click', () => {
	const isHidden = passwordInput.type === 'password';
	passwordInput.type = isHidden ? 'text' : 'password';
	confirmPasswordInput.type = isHidden ? 'text' : 'password';
	togglePasswordButton.textContent = isHidden ? 'Hide' : 'Show';
	togglePasswordButton.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
});

[fullNameInput, emailInput, passwordInput, confirmPasswordInput].forEach((input) => {
	input.addEventListener('input', () => {
		setStatus('', null);
	});
});

agreeTermsInput.addEventListener('change', () => {
	clearFieldError(agreeTermsInput, termsError);
	setStatus('', null);
});

signinForm.addEventListener('submit', async (event) => {
	event.preventDefault();

	if (!validateForm()) {
		setStatus('Please fix the highlighted fields.', 'error');
		return;
	}

	signinButton.disabled = true;
	setStatus('Creating your account...', null);

	try {
		const response = await fetch(SIGNUP_API_URL, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify({
				full_name: fullNameInput.value.trim(),
				email: emailInput.value.trim(),
				password: passwordInput.value,
			}),
		});

		let payload = {};
		try {
			payload = await response.json();
		} catch {
			payload = {};
		}

		if (!response.ok) {
			throw new Error(payload.detail || 'Signup failed.');
		}

		setStatus('Account created. Redirecting to login...', 'success');
		setTimeout(() => {
			window.location.href = LOGIN_PAGE_URL;
		}, 600);
	} catch (error) {
		setStatus(error.message || 'Unable to create account right now.', 'error');
		signinButton.disabled = false;
	}
});

themeToggle.addEventListener('click', () => {
	const isNowLight = document.body.classList.toggle('light-theme');
	localStorage.setItem('theme', isNowLight ? 'light' : 'dark');
	updateThemeToggle();
});

applySavedTheme();
initMathBackground();
window.addEventListener('resize', initMathBackground);
