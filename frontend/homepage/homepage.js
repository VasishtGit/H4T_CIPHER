const dropZone = document.getElementById('dropZone');
const imageUpload = document.getElementById('imageUpload');
const previewImage = document.getElementById('previewImage');
const previewPlaceholder = document.getElementById('previewPlaceholder');
const dropPromptButton = document.querySelector('.drop-prompt-button');
const uploadButton = document.getElementById('uploadButton');
const themeToggle = document.getElementById('themeToggle');
const mathBackground = document.getElementById('mathBackground');
const API_BASE_URL = 'http://localhost:8000';
const statusLine = document.querySelector('.status-line') || (() => {
	const element = document.createElement('div');
	element.className = 'status-line';
	dropZone.insertAdjacentElement('afterend', element);
	return element;
})();

const solutionCard = document.getElementById('solutionCard');
const manualEquationInput = document.getElementById('manualEquation');
const manualSolveButton = document.getElementById('manualSolveButton');

function renderResult(s) {
	if (!s) {
		solutionCard.textContent = 'No result available';
		return;
	}

	const equationText = s.equation || 'Could not identify a specific linear equation';
	const rawText = s.raw_result || s.equation || 'N/A';
	const sourceText = s.equation_source || 'unknown';

	solutionCard.innerHTML = `
		<h2>Solution</h2>
		<p><strong>Equation source:</strong> ${sourceText}</p>
		<p><strong>Equation:</strong> ${equationText}</p>
		<p><strong>Slope (m):</strong> ${s.slope ?? 'N/A'}</p>
		<p><strong>Y-intercept:</strong> ${s.y_intercept ?? 'N/A'}</p>
		<p><strong>X-intercept:</strong> ${s.x_intercept ?? 'N/A'}</p>
		<p><strong>AI raw text:</strong> ${rawText ? `<code>${rawText}</code>` : 'N/A'}</p>
		<p><strong>OCR text:</strong> ${(s.ocr_text || 'N/A').replace(/\n/g, ' ' )}</p>
		<details><summary>Steps</summary>
			<ol>${(s.steps || []).map((step) => `<li>${step}</li>`).join('')}</ol>
		</details>
	`;
}

let selectedFiles = [];
let hasParallaxListener = false;

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
 	`<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<line class="math-c" x1="18" y1="118" x2="204" y2="118"></line>
		<line class="math-c" x1="26" y1="16" x2="26" y2="126"></line>
		<path class="math-a" d="M30 108 C72 88, 96 34, 128 44 C154 52, 176 84, 196 72"></path>
		<polyline class="math-b" points="40,92 72,78 96,54 130,46 160,62 186,82"></polyline>
	</svg>`,
	`<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<g class="math-c">
			<line x1="0" y1="28" x2="220" y2="28"></line>
			<line x1="0" y1="56" x2="220" y2="56"></line>
			<line x1="0" y1="84" x2="220" y2="84"></line>
			<line x1="0" y1="112" x2="220" y2="112"></line>
		</g>
		<path class="math-b" d="M4 104 L46 88 L82 66 L116 72 L152 46 L188 38 L216 30"></path>
	</svg>`,
];

function randomInRange(min, max) {
	return Math.random() * (max - min) + min;
}

function buildRandomGraphSvg() {
	const baselineY = randomInRange(96, 122).toFixed(1);
	const axisX = randomInRange(16, 34).toFixed(1);
	const pointCount = Math.floor(randomInRange(5, 8));
	const points = [];

	for (let index = 0; index < pointCount; index += 1) {
		const x = (20 + index * (180 / (pointCount - 1))).toFixed(1);
		const y = randomInRange(22, 108).toFixed(1);
		points.push(`${x},${y}`);
	}

	return `<svg viewBox="0 0 220 140" preserveAspectRatio="none" aria-hidden="true">
		<line class="math-c" x1="12" y1="${baselineY}" x2="208" y2="${baselineY}"></line>
		<line class="math-c" x1="${axisX}" y1="14" x2="${axisX}" y2="126"></line>
		<polyline class="math-a" points="${points.join(' ')}"></polyline>
		<path class="math-b" d="M18 ${randomInRange(110, 120).toFixed(1)} C62 ${randomInRange(24, 72).toFixed(1)}, 138 ${randomInRange(28, 86).toFixed(1)}, 202 ${randomInRange(38, 106).toFixed(1)}"></path>
	</svg>`;
}

function createMathNode(index) {
	const element = document.createElement('div');
	element.className = 'math-float';

	const vw = window.innerWidth;
	const vh = window.innerHeight;
	const width = randomInRange(110, 250);
	const height = randomInRange(78, 160);
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
	element.style.setProperty('--alpha', `${randomInRange(0.3, 0.56).toFixed(3)}`);
	element.style.setProperty('--blur', `${randomInRange(0, 0.45).toFixed(2)}px`);
	element.dataset.depth = randomInRange(0.2, 1).toFixed(3);

	const useProceduralGraph = Math.random() > 0.45;
	element.innerHTML = useProceduralGraph
		? buildRandomGraphSvg()
		: mathSvgTemplates[Math.floor(randomInRange(0, mathSvgTemplates.length))];

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
	const count = window.innerWidth < 700 ? 24 : window.innerWidth < 1100 ? 34 : 46;
	mathBackground.innerHTML = '';

	for (let index = 0; index < count; index += 1) {
		mathBackground.appendChild(createMathNode(index));
	}

	if (!prefersReducedMotion && !hasParallaxListener) {
		window.addEventListener('mousemove', applyMathParallax, { passive: true });
		hasParallaxListener = true;
	}
}

function syncUploadButton() {
	uploadButton.disabled = selectedFiles.length === 0;
}

function updateThemeButtonLabel() {
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
	updateThemeButtonLabel();
}

function showPreview(file) {
	if (!file) {
		previewImage.removeAttribute('src');
		previewImage.style.display = 'none';
		previewPlaceholder.style.display = 'grid';
		return;
	}

	const reader = new FileReader();
	reader.onload = () => {
		previewImage.src = reader.result;
		previewImage.style.display = 'block';
		previewPlaceholder.style.display = 'none';
	};
	reader.readAsDataURL(file);
}

function setSelectedFiles(files) {
	selectedFiles = files;
	showPreview(files[0] || null);
	syncUploadButton();
}

imageUpload.addEventListener('change', () => {
	const files = Array.from(imageUpload.files || []).filter((item) => item.type.startsWith('image/'));
	setSelectedFiles(files);
});

['dragenter', 'dragover'].forEach((eventName) => {
	dropZone.addEventListener(eventName, (event) => {
		event.preventDefault();
		dropZone.classList.add('is-active');
	});
});

['dragleave', 'drop'].forEach((eventName) => {
	dropZone.addEventListener(eventName, (event) => {
		event.preventDefault();
		if (eventName === 'drop') {
			const files = Array.from(event.dataTransfer.files || []).filter((item) => item.type.startsWith('image/'));
			if (files.length) {
				const dataTransfer = new DataTransfer();
				files.forEach((file) => dataTransfer.items.add(file));
				imageUpload.files = dataTransfer.files;
				setSelectedFiles(files);
			}
		}
		dropZone.classList.remove('is-active');
	});
});

dropPromptButton.addEventListener('click', (event) => {
	event.preventDefault();
	imageUpload.click();
});

uploadButton.addEventListener('click', async () => {
	if (!selectedFiles.length) {
		return;
	}

	const formData = new FormData();
	selectedFiles.forEach((file) => formData.append('images', file));
	statusLine.textContent = `Uploading ${selectedFiles.length} image${selectedFiles.length > 1 ? 's' : ''}...`;
	solutionCard.innerHTML = '';

	try {
		const response = await fetch(`${API_BASE_URL}/upload`, {
			method: 'POST',
			body: formData,
		});

		if (!response.ok) {
			const err = await response.json().catch(() => ({}));
			throw new Error(err.detail || 'Upload failed');
		}

		const result = await response.json();
		statusLine.textContent = 'Image processed successfully.';

		if (result.solution) {
			renderResult(result.solution);
		} else {
			solutionCard.textContent = JSON.stringify(result, null, 2);
		}
	} catch (error) {
		statusLine.textContent = `Error: ${error.message}`;
		solutionCard.innerHTML = '<p style="color:red;">Unable to process the image. Confirm backend service is running on http://localhost:8000.</p>';
	}
});

manualSolveButton.addEventListener('click', async () => {
	const equationText = manualEquationInput.value.trim();
	if (!equationText) {
		statusLine.textContent = 'Please enter a valid equation first.';
		return;
	}

	statusLine.textContent = 'Solving manual equation...';
	try {
		const response = await fetch(`${API_BASE_URL}/solve_text`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ equation: equationText }),
		});

		if (!response.ok) {
			const err = await response.json().catch(() => ({}));
			throw new Error(err.detail || 'Manual equation solve failed');
		}

		const result = await response.json();
		statusLine.textContent = 'Manual equation processed.';
		if (result.solution) {
			renderResult(result.solution);
		} else {
			solutionCard.textContent = JSON.stringify(result, null, 2);
		}
	} catch (error) {
		statusLine.textContent = `Error: ${error.message}`;
		solutionCard.innerHTML = '<p style="color:red;">Manual equation processing failed. Check console for details.</p>';
	}
});

themeToggle.addEventListener('click', () => {
	const isNowLight = document.body.classList.toggle('light-theme');
	localStorage.setItem('theme', isNowLight ? 'light' : 'dark');
	updateThemeButtonLabel();
});

applySavedTheme();
syncUploadButton();
initMathBackground();
window.addEventListener('resize', initMathBackground);
