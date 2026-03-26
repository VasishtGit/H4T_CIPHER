const activeQuestion = document.getElementById('activeQuestion');
const questionHistory = document.getElementById('questionHistory');
const explainContent = document.getElementById('explainContent');
const themeToggle = document.getElementById('themeToggle');
const floatingChatWidget = document.getElementById('floatingChatWidget');
const floatingChatIcon = document.getElementById('floatingChatIcon');
const floatingChatPanel = document.getElementById('floatingChatPanel');
const floatingChatClose = document.getElementById('floatingChatClose');
const floatingChatMessages = document.getElementById('floatingChatMessages');
const floatingChatTyping = document.getElementById('floatingChatTyping');
const floatingChatForm = document.getElementById('floatingChatForm');
const floatingChatInput = document.getElementById('floatingChatInput');

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
