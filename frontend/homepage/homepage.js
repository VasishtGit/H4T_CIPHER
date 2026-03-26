const dropZone = document.getElementById('dropZone');
const imageUpload = document.getElementById('imageUpload');
const previewImage = document.getElementById('previewImage');
const previewPlaceholder = document.getElementById('previewPlaceholder');
const dropPromptButton = document.querySelector('.drop-prompt-button');
const uploadButton = document.getElementById('uploadButton');
const themeToggle = document.getElementById('themeToggle');
const statusLine = document.querySelector('.status-line') || (() => {
	const element = document.createElement('div');
	element.className = 'status-line';
	dropZone.insertAdjacentElement('afterend', element);
	return element;
})();

let selectedFiles = [];

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

	try {
		const response = await fetch('/upload', {
			method: 'POST',
			body: formData,
		});

		if (!response.ok) {
			throw new Error('Upload failed');
		}

		statusLine.textContent = 'Image upload successful.';
	} catch (error) {
		statusLine.textContent = 'Upload endpoint is not available yet.';
	}
});

themeToggle.addEventListener('click', () => {
	const isNowLight = document.body.classList.toggle('light-theme');
	localStorage.setItem('theme', isNowLight ? 'light' : 'dark');
	updateThemeButtonLabel();
});

applySavedTheme();
syncUploadButton();
