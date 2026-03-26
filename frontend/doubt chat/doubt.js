const chatWidget = document.getElementById('chatWidget');
const chatToggle = document.getElementById('chatToggle');
const chatClose = document.getElementById('chatClose');
const chatPanel = document.getElementById('chatPanel');
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const typingIndicator = document.getElementById('typingIndicator');

function applySavedTheme() {
	const savedTheme = localStorage.getItem('theme');
	if (savedTheme === 'light') {
		document.body.classList.add('light-theme');
	} else {
		document.body.classList.remove('light-theme');
	}
}

function setChatOpen(open) {
	chatWidget.classList.toggle('open', open);
	chatToggle.setAttribute('aria-expanded', String(open));
	chatPanel.setAttribute('aria-hidden', String(!open));

	if (open) {
		setTimeout(() => chatInput.focus(), 180);
	}
}

function scrollToLatest() {
	chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(content, sender) {
	const article = document.createElement('article');
	article.className = `message ${sender}`;

	const text = document.createElement('p');
	text.textContent = content;

	article.appendChild(text);
	chatMessages.appendChild(article);
	scrollToLatest();
}

function getBotReply(message) {
	const msg = message.toLowerCase();

	if (msg.includes('graph')) {
		return 'For graph problems, start by identifying known points, slope, and axis intercepts before applying formulas.';
	}
	if (msg.includes('equation')) {
		return 'Break the equation into smaller steps and isolate one variable at a time to avoid mistakes.';
	}
	if (msg.includes('hello') || msg.includes('hi')) {
		return 'Hi! Share your question and I will guide you step by step.';
	}

	return 'Thanks for your question. I can help with graph concepts, equations, and problem-solving steps.';
}

chatToggle.addEventListener('click', () => {
	const isOpen = chatWidget.classList.contains('open');
	setChatOpen(!isOpen);
});

chatClose.addEventListener('click', () => {
	setChatOpen(false);
});

chatForm.addEventListener('submit', (event) => {
	event.preventDefault();

	const message = chatInput.value.trim();
	if (!message) {
		return;
	}

	addMessage(message, 'user');
	chatInput.value = '';

	typingIndicator.hidden = false;
	scrollToLatest();

	setTimeout(() => {
		typingIndicator.hidden = true;
		addMessage(getBotReply(message), 'bot');
	}, 900);
});

applySavedTheme();
setChatOpen(true);
