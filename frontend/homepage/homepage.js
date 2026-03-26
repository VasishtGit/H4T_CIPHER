const dropZone = document.getElementById('dropZone');
const imageUpload = document.getElementById('imageUpload');
const previewImage = document.getElementById('previewImage');
const previewPlaceholder = document.getElementById('previewPlaceholder');
const uploadButton = document.getElementById('uploadButton');
const themeToggle = document.getElementById('themeToggle');
const statusLine = document.querySelector('.status-line') || (() => {
	const element = document.createElement('div');
	element.className = 'status-line';
	dropZone.insertAdjacentElement('afterend', element);
	return element;
})();

let selectedFiles = [];

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

function syncButtons() {
	const hasFile = selectedFiles.length > 0;
	uploadButton.disabled = !hasFile;
}

function showPreview(file) {
	if (!file) {
		selectedFiles = [];
		previewImage.removeAttribute('src');
		previewImage.style.display = 'none';
		previewPlaceholder.style.display = 'grid';
		syncButtons();
		return;
	}

	selectedFiles = [file];
	const reader = new FileReader();
	reader.onload = () => {
		previewImage.src = reader.result;
		previewImage.style.display = 'block';
		previewPlaceholder.style.display = 'none';
		syncButtons();
	};
	reader.readAsDataURL(file);
}

imageUpload.addEventListener('change', () => {
	showPreview(imageUpload.files[0]);
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
			const file = Array.from(event.dataTransfer.files || []).find((item) => item.type.startsWith('image/'));
			if (file) {
				const dataTransfer = new DataTransfer();
				dataTransfer.items.add(file);
				imageUpload.files = dataTransfer.files;
				showPreview(file);
			}
		}
		dropZone.classList.remove('is-active');
	});
});

dropZone.addEventListener('click', (event) => {
	if (event.target !== imageUpload) {
		imageUpload.click();
	}
});

uploadButton.addEventListener('click', () => {
	if (!selectedFiles.length) {
		return;
	}

	statusLine.textContent = `Ready to upload ${selectedFiles.length} selected image${selectedFiles.length > 1 ? 's' : ''}.`;
});

themeToggle.addEventListener('click', () => {
	const isNowLight = document.body.classList.toggle('light-theme');
	localStorage.setItem('theme', isNowLight ? 'light' : 'dark');
	updateThemeButtonLabel();
});

applySavedTheme();

syncButtons();
