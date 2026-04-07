const uploadForm = document.getElementById('uploadForm');
const imageInput = document.getElementById('imageInput');
const uploadButton = document.getElementById('uploadButton');
const statusEl = document.getElementById('status');
const userIndicator = document.getElementById('userIndicator');
const logoutButton = document.getElementById('logoutButton');

const QUESTION_IMAGE_DATA_KEY = 'questionImageDataUrl';
const QUESTION_IMAGE_NAME_KEY = 'questionImageName';
const QUESTION_IMAGE_TYPE_KEY = 'questionImageType';
const EXPLAIN_PAGE_URL = '../explanation page/explain.html';
const LOGIN_PAGE_URL = '../login/login.html';
const AUTH_BASE_URL = 'https://h4t-cipher-1.onrender.com';
const AUTH_ME_URL = `${AUTH_BASE_URL}/me`;
const AUTH_LOGOUT_URL = `${AUTH_BASE_URL}/logout`;
const TOKEN_KEY = 'token';

function getAuthHeaders() {
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function setStatus(message) {
    statusEl.textContent = message;
}

function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Unable to read image file.'));
        reader.readAsDataURL(file);
    });
}

uploadForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const file = imageInput.files && imageInput.files[0];
    if (!file) {
        setStatus('Please select an image first.');
        return;
    }

    uploadButton.disabled = true;
    setStatus('Preparing image...');

    try {
        const imageDataUrl = await readFileAsDataUrl(file);
        sessionStorage.setItem(QUESTION_IMAGE_DATA_KEY, imageDataUrl);
        sessionStorage.setItem(QUESTION_IMAGE_NAME_KEY, file.name || 'question.png');
        sessionStorage.setItem(QUESTION_IMAGE_TYPE_KEY, file.type || 'image/png');

        setStatus('Redirecting to explanation page...');
        window.location.href = EXPLAIN_PAGE_URL;

    } catch (error) {
        setStatus(`Error: ${error.message}`);
    } finally {
        uploadButton.disabled = false;
    }
});

async function ensureAuthenticated() {
    try {
        const response = await fetch(AUTH_ME_URL, { headers: getAuthHeaders() });
        if (!response.ok) {
            window.location.href = LOGIN_PAGE_URL;
            return false;
        }

        const payload = await response.json();
        const fullName = payload?.user?.full_name || payload?.user?.email || 'User';
        if (userIndicator) {
            userIndicator.textContent = `Signed in as ${fullName}`;
        }
        return true;
    } catch {
        window.location.href = LOGIN_PAGE_URL;
        return false;
    }
}

if (logoutButton) {
    logoutButton.addEventListener('click', async () => {
        try {
            await fetch(AUTH_LOGOUT_URL, { method: 'POST', headers: getAuthHeaders() });
        } finally {
            localStorage.removeItem(TOKEN_KEY);
            window.location.href = LOGIN_PAGE_URL;
        }
    });
}

ensureAuthenticated();