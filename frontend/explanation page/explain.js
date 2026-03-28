const activeQuestion = document.getElementById('activeQuestion');
const questionHistory = document.getElementById('questionHistory');
const explainContent = document.getElementById('explainContent');
const themeToggle = document.getElementById('themeToggle');
const mathBackground = document.getElementById('mathBackground');
const floatingChatWidget = document.getElementById('floatingChatWidget');
const floatingChatIcon = document.getElementById('floatingChatIcon');
const floatingChatPanel = document.getElementById('floatingChatPanel');
const floatingChatClose = document.getElementById('floatingChatClose');
const floatingChatMessages = document.getElementById('floatingChatMessages');
const floatingChatTyping = document.getElementById('floatingChatTyping');
const floatingChatForm = document.getElementById('floatingChatForm');
const floatingChatInput = document.getElementById('floatingChatInput');
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

function createMathNode() {
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
		mathBackground.appendChild(createMathNode());
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

function setFloatingChatOpen(open) {
	floatingChatWidget.classList.toggle('open', open);
	floatingChatIcon.setAttribute('aria-expanded', String(open));
	floatingChatPanel.setAttribute('aria-hidden', String(!open));

	if (open) {
		setTimeout(() => floatingChatInput.focus(), 170);
	}
}

function scrollFloatingChatToLatest() {
	floatingChatMessages.scrollTop = floatingChatMessages.scrollHeight;
}

function addFloatingChatMessage(content, sender) {
	const article = document.createElement('article');
	article.className = `floating-chat-message ${sender}`;

	const text = document.createElement('p');
	text.textContent = content;

	article.appendChild(text);
	floatingChatMessages.appendChild(article);
	scrollFloatingChatToLatest();
}

function getFloatingBotReply(message) {
	const msg = message.toLowerCase();

	if (msg.includes('slope')) {
		return 'Slope tells us how quickly y changes. For slope 4, y goes up 4 for each +1 in x.';
	}
	if (msg.includes('graph')) {
		return 'Plot known points first, then use slope direction to build the line and verify intercepts.';
	}
	if (msg.includes('equation') || msg.includes('formula')) {
		return 'Use point-slope form y - y1 = m(x - x1), then simplify into y = mx + b if needed.';
	}

	return 'I can help step-by-step. Share exactly where you are stuck and I will break it down clearly.';
}

function setActiveHistoryButton(nextButton) {
	const allButtons = questionHistory.querySelectorAll('.history-item');
	allButtons.forEach((button) => button.classList.remove('is-active'));
	nextButton.classList.add('is-active');
}

function updateExplanationForQuestion(questionText) {
	if (questionText.toLowerCase().includes('vertex')) {
		explainContent.innerHTML = `
			<h3>Given Expression</h3>
			<p>y = x^2 - 6x + 5</p>
			<h3>Convert to Vertex Form</h3>
			<p>Complete the square:</p>
			<p class="formula">y = (x - 3)^2 - 4</p>
			<h3>Result</h3>
			<p>Vertex is <strong>(3, -4)</strong> and axis of symmetry is <strong>x = 3</strong>.</p>
		`;
		return;
	}

	if (questionText.toLowerCase().includes('intersects')) {
		explainContent.innerHTML = `
			<h3>Set Equations Equal</h3>
			<p>2x + 1 = -x + 7</p>
			<h3>Solve for x</h3>
			<p class="formula">3x = 6  =>  x = 2</p>
			<h3>Find y</h3>
			<p>Substitute x = 2 into y = 2x + 1:</p>
			<p class="formula">y = 5</p>
			<h3>Intersection Point</h3>
			<p>The lines intersect at <strong>(2,5)</strong>.</p>
		`;
		return;
	}

	explainContent.innerHTML = `
		<h3>Given Information</h3>
		<p>We are given one point on the line: <strong>(2,3)</strong> and slope <strong>m = 4</strong>.</p>
		<h3>Apply Point-Slope Form</h3>
		<p class="formula">y - y₁ = m(x - x₁)</p>
		<p class="formula">y - 3 = 4(x - 2)</p>
		<h3>Simplify</h3>
		<p class="formula">y - 3 = 4x - 8</p>
		<p class="formula">y = 4x - 5</p>
		<h3>Final Answer</h3>
		<p>The required line equation is <strong>y = 4x - 5</strong>.</p>
	`;
}

questionHistory.addEventListener('click', (event) => {
	const button = event.target.closest('.history-item');
	if (!button) {
		return;
	}

	const questionText = button.dataset.question;
	activeQuestion.textContent = questionText;
	setActiveHistoryButton(button);
	updateExplanationForQuestion(questionText);
});

themeToggle.addEventListener('click', () => {
	const isNowLight = document.body.classList.toggle('light-theme');
	localStorage.setItem('theme', isNowLight ? 'light' : 'dark');
	updateThemeToggle();
});

floatingChatIcon.addEventListener('click', () => {
	const isOpen = floatingChatWidget.classList.contains('open');
	setFloatingChatOpen(!isOpen);
});

floatingChatClose.addEventListener('click', () => {
	setFloatingChatOpen(false);
});

floatingChatForm.addEventListener('submit', (event) => {
	event.preventDefault();

	const message = floatingChatInput.value.trim();
	if (!message) {
		return;
	}

	addFloatingChatMessage(message, 'user');
	floatingChatInput.value = '';

	floatingChatTyping.hidden = false;
	scrollFloatingChatToLatest();

	setTimeout(() => {
		floatingChatTyping.hidden = true;
		addFloatingChatMessage(getFloatingBotReply(message), 'bot');
	}, 850);
});

applySavedTheme();
initMathBackground();
window.addEventListener('resize', initMathBackground);
