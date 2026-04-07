const activeQuestion = document.getElementById('activeQuestion');
const explainContent = document.getElementById('explainContent');
const resultVideo = document.getElementById('resultVideo');
const resultVideoSource = document.getElementById('resultVideoSource');
const videoStatus = document.getElementById('videoStatus');
const generateVideoButton = document.getElementById('generateVideoButton');
const uploadedQuestionImage = document.getElementById('uploadedQuestionImage');
const uploadedImageCaption = document.getElementById('uploadedImageCaption');
const explanationLoader = document.getElementById('explanationLoader');
const explanationLoaderBar = document.getElementById('explanationLoaderBar');
const explanationLoaderTime = document.getElementById('explanationLoaderTime');
const explanationLoaderLabel = document.getElementById('explanationLoaderLabel');
const videoLoader = document.getElementById('videoLoader');
const videoLoaderBar = document.getElementById('videoLoaderBar');
const videoLoaderTime = document.getElementById('videoLoaderTime');
const videoLoaderLabel = document.getElementById('videoLoaderLabel');
const userIndicator = document.getElementById('userIndicator');
const logoutButton = document.getElementById('logoutButton');

const QUESTION_IMAGE_DATA_KEY = 'questionImageDataUrl';
const QUESTION_IMAGE_NAME_KEY = 'questionImageName';
const QUESTION_IMAGE_TYPE_KEY = 'questionImageType';
const LAST_IMAGE_DATA_KEY = 'lastUploadedImageDataUrl';
const LAST_IMAGE_NAME_KEY = 'lastUploadedImageName';
const LAST_IMAGE_TYPE_KEY = 'lastUploadedImageType';
const LATEST_EXPLANATION_KEY = 'latestExplanationText';
const LATEST_EXPLANATION_MODEL_KEY = 'latestExplanationModel';
const LATEST_DESCRIPTION_KEY = 'latestQuestionDescription';

const UPLOAD_URL = 'http://localhost:8000/upload';
const GENERATE_VIDEO_URL = 'http://localhost:8001/generate-video-v2';
const VIDEO_STREAM_URL = 'http://localhost:8001/video';
const AUTH_BASE_URL = 'https://h4t-cipher-1.onrender.com';
const AUTH_ME_URL = `${AUTH_BASE_URL}/me`;
const AUTH_LOGOUT_URL = `${AUTH_BASE_URL}/logout`;
const LOGIN_PAGE_URL = '../login/login.html';

let pipelineStarted = false;
let hasVideoEventBindings = false;
let currentVideoObjectUrl = '';
let explanationLoaderTimerId = null;
let explanationLoaderStartTs = 0;
let videoLoaderTimerId = null;
let videoLoaderStartTs = 0;
let latestVideoRequestPayload = null;

const EXPLANATION_LOADING_MS = 90_000;
const VIDEO_LOADING_MS = 120_000;
const VIDEO_404_FAILURE_LIMIT = 5;

function setVideoStatus(text) {
	if (videoStatus) {
		videoStatus.textContent = text;
	}
}

function setGenerateVideoButtonState(enabled, label = 'Generate Video Explanation') {
	if (!generateVideoButton) {
		return;
	}
	generateVideoButton.disabled = !enabled;
	generateVideoButton.textContent = label;
}

function formatRemainingTime(ms) {
	const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
	const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
	const seconds = String(totalSeconds % 60).padStart(2, '0');
	return `${minutes}:${seconds}`;
}

function stopExplanationLoader() {
	if (explanationLoaderTimerId) {
		clearInterval(explanationLoaderTimerId);
		explanationLoaderTimerId = null;
	}
	if (explanationLoader) {
		explanationLoader.hidden = true;
	}
}

function startExplanationLoader(label = 'Analyzing image...') {
	stopExplanationLoader();
	explanationLoaderStartTs = Date.now();

	if (!explanationLoader || !explanationLoaderBar || !explanationLoaderTime) {
		return;
	}

	explanationLoader.hidden = false;
	if (explanationLoaderLabel) {
		explanationLoaderLabel.textContent = label;
	}
	explanationLoaderBar.style.width = '0%';
	explanationLoaderTime.textContent = formatRemainingTime(EXPLANATION_LOADING_MS);

	explanationLoaderTimerId = setInterval(() => {
		const elapsed = Date.now() - explanationLoaderStartTs;
		const remaining = EXPLANATION_LOADING_MS - elapsed;
		const progress = Math.min(100, (elapsed / EXPLANATION_LOADING_MS) * 100);
		explanationLoaderBar.style.width = `${progress.toFixed(2)}%`;
		explanationLoaderTime.textContent = formatRemainingTime(remaining);

		if (remaining <= 0) {
			clearInterval(explanationLoaderTimerId);
			explanationLoaderTimerId = null;
			if (explanationLoaderLabel) {
				explanationLoaderLabel.textContent = 'Still working...';
			}
		}
	}, 250);
}

function stopVideoLoader() {
	if (videoLoaderTimerId) {
		clearInterval(videoLoaderTimerId);
		videoLoaderTimerId = null;
	}
	if (videoLoader) {
		videoLoader.hidden = true;
	}
}

function startVideoLoader(label = 'Generating video...') {
	stopVideoLoader();
	videoLoaderStartTs = Date.now();

	if (!videoLoader || !videoLoaderBar || !videoLoaderTime) {
		return;
	}

	videoLoader.hidden = false;
	if (videoLoaderLabel) {
		videoLoaderLabel.textContent = label;
	}
	videoLoaderBar.style.width = '0%';
	videoLoaderTime.textContent = formatRemainingTime(VIDEO_LOADING_MS);

	videoLoaderTimerId = setInterval(() => {
		const elapsed = Date.now() - videoLoaderStartTs;
		const remaining = VIDEO_LOADING_MS - elapsed;
		const progress = Math.min(100, (elapsed / VIDEO_LOADING_MS) * 100);
		videoLoaderBar.style.width = `${progress.toFixed(2)}%`;
		videoLoaderTime.textContent = formatRemainingTime(remaining);

		if (remaining <= 0) {
			clearInterval(videoLoaderTimerId);
			videoLoaderTimerId = null;
			if (videoLoaderLabel) {
				videoLoaderLabel.textContent = 'Still processing...';
			}
		}
	}, 250);
}

function escapeHtml(value) {
	return String(value)
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;');
}

function sleep(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

function applyInlineMarkdown(escapedText) {
	let output = escapedText;
	output = output.replace(/`([^`]+)`/g, '<code>$1</code>');
	output = output.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
	output = output.replace(/\*([^*]+)\*/g, '<em>$1</em>');
	output = output.replace(/\\\((.+?)\\\)/g, (_, expr) => `<code>${normalizeMathExpression(expr)}</code>`);
	output = output.replace(/\$(.+?)\$/g, (_, expr) => `<code>${normalizeMathExpression(expr)}</code>`);
	return output;
}

function normalizeMathExpression(input) {
	let text = input || '';
	text = text.replace(/\\text\{([^}]+)\}/g, '$1');
	text = text.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)');
	text = text.replace(/\\cdot|\\times/g, '*');
	text = text.replace(/\\approx/g, '~=');
	text = text.replace(/\\left|\\right/g, '');
	text = text.replace(/[{}]/g, '');
	text = text.replace(/\\/g, '');
	text = text.replace(/\s+/g, ' ').trim();
	return escapeHtml(text);
}

function markdownToSafeHtml(markdownText) {
	const escaped = escapeHtml(markdownText || '');
	const lines = escaped.split(/\r?\n/);
	const htmlParts = [];
	let inUl = false;
	let inOl = false;
	let inCode = false;
	let inMath = false;
	const mathLines = [];

	const closeLists = () => {
		if (inUl) {
			htmlParts.push('</ul>');
			inUl = false;
		}
		if (inOl) {
			htmlParts.push('</ol>');
			inOl = false;
		}
	};

	for (const rawLine of lines) {
		const line = rawLine.trimEnd();
		const trimmed = line.trim();

		if (trimmed === '$$') {
			closeLists();
			if (!inMath) {
				inMath = true;
				mathLines.length = 0;
			} else {
				const normalizedMath = normalizeMathExpression(mathLines.join(' '));
				htmlParts.push(`<pre class="api-output math-output">${normalizedMath}</pre>`);
				inMath = false;
			}
			continue;
		}

		if (inMath) {
			mathLines.push(line);
			continue;
		}

		if (line.trim().startsWith('```')) {
			closeLists();
			if (!inCode) {
				htmlParts.push('<pre class="api-output"><code>');
				inCode = true;
			} else {
				htmlParts.push('</code></pre>');
				inCode = false;
			}
			continue;
		}

		if (inCode) {
			htmlParts.push(`${line}\n`);
			continue;
		}

		if (trimmed.length === 0) {
			closeLists();
			continue;
		}

		const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
		if (headingMatch) {
			closeLists();
			const level = headingMatch[1].length;
			htmlParts.push(`<h${level}>${applyInlineMarkdown(headingMatch[2])}</h${level}>`);
			continue;
		}

		const ulMatch = line.match(/^[-*+]\s+(.*)$/);
		if (ulMatch) {
			if (inOl) {
				htmlParts.push('</ol>');
				inOl = false;
			}
			if (!inUl) {
				htmlParts.push('<ul>');
				inUl = true;
			}
			htmlParts.push(`<li>${applyInlineMarkdown(ulMatch[1])}</li>`);
			continue;
		}

		const olMatch = line.match(/^\d+\.\s+(.*)$/);
		if (olMatch) {
			if (inUl) {
				htmlParts.push('</ul>');
				inUl = false;
			}
			if (!inOl) {
				htmlParts.push('<ol>');
				inOl = true;
			}
			htmlParts.push(`<li>${applyInlineMarkdown(olMatch[1])}</li>`);
			continue;
		}

		closeLists();
		htmlParts.push(`<p>${applyInlineMarkdown(line)}</p>`);
	}

	closeLists();
	if (inCode) {
		htmlParts.push('</code></pre>');
	}
	if (inMath && mathLines.length > 0) {
		const normalizedMath = normalizeMathExpression(mathLines.join(' '));
		htmlParts.push(`<pre class="api-output math-output">${normalizedMath}</pre>`);
	}

	return htmlParts.join('\n');
}

function renderExplanation(explanationText, modelName) {
	if (!explainContent) {
		return;
	}

	explainContent.innerHTML = `
		<h3>Detailed Explanation</h3>
		<p class="formula">Model: ${escapeHtml(modelName || 'unknown')}</p>
		<div class="markdown-output">${markdownToSafeHtml(explanationText || 'No explanation returned.')}</div>
	`;
}

function setUploadedImagePreview(dataUrl, fileName) {
	if (!uploadedQuestionImage || !uploadedImageCaption) {
		return;
	}

	if (!dataUrl) {
		uploadedQuestionImage.removeAttribute('src');
		uploadedQuestionImage.style.display = 'none';
		uploadedImageCaption.textContent = 'No uploaded image found.';
		return;
	}

	uploadedQuestionImage.src = dataUrl;
	uploadedQuestionImage.style.display = 'block';
	uploadedImageCaption.textContent = fileName ? `Uploaded: ${fileName}` : 'Uploaded image preview';
}

function dataUrlToFile(dataUrl, fileName, fileType) {
	if (!dataUrl || !dataUrl.includes(',')) {
		throw new Error('Invalid image payload.');
	}

	const [meta, b64Data] = dataUrl.split(',');
	const detectedType = meta.match(/^data:(.*?);base64$/)?.[1] || fileType || 'image/png';
	const binary = atob(b64Data);
	const bytes = new Uint8Array(binary.length);

	for (let index = 0; index < binary.length; index += 1) {
		bytes[index] = binary.charCodeAt(index);
	}

	return new File([bytes], fileName || 'question.png', { type: detectedType });
}

async function parseJsonSafe(response) {
	const text = await response.text();
	if (!text) {
		return {};
	}

	try {
		return JSON.parse(text);
	} catch {
		return { detail: text };
	}
}

function bindVideoDebugEvents() {
	if (!resultVideo || hasVideoEventBindings) {
		return;
	}

	hasVideoEventBindings = true;

	resultVideo.addEventListener('loadedmetadata', () => {
		setVideoStatus('Video metadata loaded. Press play.');
	});

	resultVideo.addEventListener('canplay', () => {
		setVideoStatus('Video ready. Press play.');
	});

	resultVideo.addEventListener('error', () => {
		const mediaError = resultVideo.error;
		const code = mediaError ? mediaError.code : 'unknown';
		setVideoStatus(`Video playback error (code ${code}).`);
	});
}

async function setVideoSourceWithFallback(streamUrl) {
	if (!resultVideo) {
		return;
	}

	bindVideoDebugEvents();
	resultVideo.crossOrigin = 'anonymous';
	resultVideo.playsInline = true;

	if (currentVideoObjectUrl) {
		URL.revokeObjectURL(currentVideoObjectUrl);
		currentVideoObjectUrl = '';
	}

	const cacheBustedUrl = `${streamUrl}?t=${Date.now()}`;
	if (resultVideoSource) {
		resultVideoSource.removeAttribute('src');
	}
	resultVideo.src = cacheBustedUrl;
	resultVideo.load();

	const waitForLoad = new Promise((resolve, reject) => {
		const onCanPlay = () => {
			cleanup();
			resolve(true);
		};

		const onError = () => {
			cleanup();
			reject(new Error('video_element_error'));
		};

		const cleanup = () => {
			resultVideo.removeEventListener('canplay', onCanPlay);
			resultVideo.removeEventListener('error', onError);
		};

		resultVideo.addEventListener('canplay', onCanPlay, { once: true });
		resultVideo.addEventListener('error', onError, { once: true });
	});

	try {
		await Promise.race([
			waitForLoad,
			new Promise((_, reject) => setTimeout(() => reject(new Error('video_load_timeout')), 10000)),
		]);
		return;
	} catch {
		setVideoStatus('Direct stream load failed. Trying fallback...');
	}

	const blobResponse = await fetch(cacheBustedUrl, { method: 'GET', cache: 'no-store' });
	if (!blobResponse.ok) {
		throw new Error(`Video fetch fallback failed: ${blobResponse.status}`);
	}

	const videoBlob = await blobResponse.blob();
	const objectUrl = URL.createObjectURL(videoBlob);
	currentVideoObjectUrl = objectUrl;
	resultVideo.removeAttribute('src');
	if (resultVideoSource) {
		resultVideoSource.removeAttribute('src');
	}
	resultVideo.src = objectUrl;
	resultVideo.load();
}

function buildVideoUrlCandidates(videoData) {
	const backendOrigin = new URL(GENERATE_VIDEO_URL, window.location.href).origin;
	const candidates = [
		videoData?.video_url,
		VIDEO_STREAM_URL,
		`${backendOrigin}/video`,
	].filter(Boolean);

	return [...new Set(candidates)];
}

async function checkVideoUrl(streamUrl) {
	const probeUrl = `${streamUrl}?probe=${Date.now()}`;
	try {
		const response = await fetch(probeUrl, {
			method: 'GET',
			headers: { Range: 'bytes=0-0' },
			credentials: 'include',
			cache: 'no-store',
		});
		return {
			ready: response.ok || response.status === 206,
			status: response.status,
		};
	} catch {
		return {
			ready: false,
			status: 0,
		};
	}
}

async function waitForAnyVideoReady(streamUrls, maxWaitMs = 30000, intervalMs = 900) {
	const start = Date.now();
	while (Date.now() - start < maxWaitMs) {
		for (const streamUrl of streamUrls) {
			const probe = await checkVideoUrl(streamUrl);
			if (probe.ready) {
				return streamUrl;
			}
		}
		await sleep(intervalMs);
	}
	return null;
}

async function waitForAnyVideoReadyWith404Limit(
	streamUrls,
	maxWaitMs = VIDEO_LOADING_MS,
	intervalMs = 900,
	max404Count = VIDEO_404_FAILURE_LIMIT,
) {
	const start = Date.now();
	let notFoundCount = 0;

	while (Date.now() - start < maxWaitMs) {
		for (const streamUrl of streamUrls) {
			const probe = await checkVideoUrl(streamUrl);
			if (probe.ready) {
				return { readyUrl: streamUrl, notFoundCount };
			}

			if (probe.status === 404) {
				notFoundCount += 1;
				if (notFoundCount >= max404Count) {
					return { readyUrl: null, notFoundCount, failedBy404: true };
				}
			}
		}

		await sleep(intervalMs);
	}

	return { readyUrl: null, notFoundCount, failedBy404: false };
}

async function tryLoadLatestGeneratedVideo() {
	const streamUrls = buildVideoUrlCandidates({});
	const readyUrl = await waitForAnyVideoReady(streamUrls, 12000, 800);

	if (!readyUrl) {
		setVideoStatus('No latest video available yet.');
		return;
	}

	try {
		await setVideoSourceWithFallback(readyUrl);
		setVideoStatus('Latest generated video loaded. Press play.');
	} catch (error) {
		setVideoStatus(`No latest video available. ${error.message || ''}`.trim());
	}
}

async function requestAndLoadVideo() {
	if (!latestVideoRequestPayload) {
		setVideoStatus('Generate explanation first, then generate video.');
		return;
	}

	const { explanation } = latestVideoRequestPayload;
	const questionDescription = latestVideoRequestPayload.questionDescription || explanation || '';
	if (!explanation || !questionDescription) {
		setVideoStatus('Missing explanation or description for video generation.');
		return;
	}

	setGenerateVideoButtonState(false, 'Generating...');
	setVideoStatus('Generating video...');
	startVideoLoader('Generating video...');

	const videoFormData = new FormData();
	videoFormData.append('explanation', explanation);
	videoFormData.append('question_description', questionDescription);
	if (latestVideoRequestPayload.graphUrl) {
		videoFormData.append('graph_url', latestVideoRequestPayload.graphUrl);
	}

	let videoResponse;
	try {
		videoResponse = await fetch(GENERATE_VIDEO_URL, {
			method: 'POST',
			credentials: 'include',
			body: videoFormData,
		});
	} catch {
		stopVideoLoader();
		setVideoStatus('Error: Unable to reach video generation service.');
		setGenerateVideoButtonState(true);
		return;
	}

	const videoData = await parseJsonSafe(videoResponse);
	if (!videoResponse.ok) {
		stopVideoLoader();
		setVideoStatus(`Error: ${videoData.detail || 'Failed to generate video.'}`);
		setGenerateVideoButtonState(true);
		return;
	}

	const streamUrls = buildVideoUrlCandidates(videoData);
	setVideoStatus('Waiting for video to become ready...');
	if (videoLoaderLabel) {
		videoLoaderLabel.textContent = 'Waiting for video stream...';
	}
	const waitResult = await waitForAnyVideoReadyWith404Limit(streamUrls, VIDEO_LOADING_MS, 900, VIDEO_404_FAILURE_LIMIT);
	const readyUrl = waitResult.readyUrl;

	if (!readyUrl) {
		stopVideoLoader();
		if (waitResult.failedBy404) {
			setVideoStatus('Video generation failed: stream returned 404 five times. Please try again.');
		} else {
			setVideoStatus('Video generation timed out after 2 minutes. Please try again.');
		}
		setGenerateVideoButtonState(true);
		return;
	}

	try {
		await setVideoSourceWithFallback(readyUrl);
		setVideoStatus('Video ready. Press play.');
	} catch (error) {
		setVideoStatus(`Error: Unable to load generated video. ${error.message || ''}`.trim());
	}

	stopVideoLoader();
	setGenerateVideoButtonState(true);
}

async function runBackendPipeline() {
	if (pipelineStarted) {
		return;
	}
	pipelineStarted = true;

	const imageDataUrl = sessionStorage.getItem(QUESTION_IMAGE_DATA_KEY);
	const imageName = sessionStorage.getItem(QUESTION_IMAGE_NAME_KEY) || 'question.png';
	const imageType = sessionStorage.getItem(QUESTION_IMAGE_TYPE_KEY) || 'image/png';
	const lastImageDataUrl = sessionStorage.getItem(LAST_IMAGE_DATA_KEY);
	const lastImageName = sessionStorage.getItem(LAST_IMAGE_NAME_KEY) || 'question.png';
	const lastImageType = sessionStorage.getItem(LAST_IMAGE_TYPE_KEY) || 'image/png';
	const cachedExplanation = sessionStorage.getItem(LATEST_EXPLANATION_KEY);
	const cachedModel = sessionStorage.getItem(LATEST_EXPLANATION_MODEL_KEY) || 'unknown';
	const cachedDescription = sessionStorage.getItem(LATEST_DESCRIPTION_KEY) || '';

	setGenerateVideoButtonState(false);

	if (!imageDataUrl) {
		if (cachedExplanation) {
			renderExplanation(cachedExplanation, cachedModel);
			latestVideoRequestPayload = {
				explanation: cachedExplanation,
				questionDescription: cachedDescription || cachedExplanation,
			};
			setGenerateVideoButtonState(true);
		} else if (explainContent) {
			explainContent.innerHTML = '<p>No uploaded image found. Please go back and upload a question image first.</p>';
		}
		if (lastImageDataUrl) {
			setUploadedImagePreview(lastImageDataUrl, lastImageName);
		} else {
			setUploadedImagePreview('', '');
		}
		await tryLoadLatestGeneratedVideo();
		return;
	}

	if (activeQuestion) {
		activeQuestion.textContent = `Uploaded question: ${imageName}`;
	}
	setUploadedImagePreview(imageDataUrl, imageName);
	sessionStorage.setItem(LAST_IMAGE_DATA_KEY, imageDataUrl);
	sessionStorage.setItem(LAST_IMAGE_NAME_KEY, imageName);
	sessionStorage.setItem(LAST_IMAGE_TYPE_KEY, imageType);
	if (explainContent) {
		explainContent.innerHTML = '<p>Analyzing your image and generating explanation...</p>';
	}
	startExplanationLoader('Analyzing image...');
	setVideoStatus('Waiting for explanation...');

	sessionStorage.removeItem(QUESTION_IMAGE_DATA_KEY);
	sessionStorage.removeItem(QUESTION_IMAGE_NAME_KEY);
	sessionStorage.removeItem(QUESTION_IMAGE_TYPE_KEY);

	const imageFile = dataUrlToFile(imageDataUrl, imageName, imageType || lastImageType);

	const uploadFormData = new FormData();
	uploadFormData.append('image', imageFile);

	let uploadResponse;
	try {
		uploadResponse = await fetch(UPLOAD_URL, {
			method: 'POST',
			credentials: 'include',
			body: uploadFormData,
		});
	} catch {
		stopExplanationLoader();
		if (explainContent) {
			explainContent.innerHTML = '<p>Explanation error: Unable to reach explanation service.</p>';
		}
		setVideoStatus('Video generation not started.');
		return;
	}

	const uploadData = await parseJsonSafe(uploadResponse);
	stopExplanationLoader();
	if (!uploadResponse.ok) {
		if (explainContent) {
			explainContent.innerHTML = `<p>Explanation error: ${escapeHtml(uploadData.detail || 'Failed to get explanation.')}</p>`;
		}
		setVideoStatus('Video generation not started.');
		return;
	}

	const explanation = uploadData.analysis || 'No explanation returned.';
	const questionDescription = uploadData.description || explanation;
	renderExplanation(explanation, uploadData.model || 'unknown');
	sessionStorage.setItem(LATEST_EXPLANATION_KEY, explanation);
	sessionStorage.setItem(LATEST_EXPLANATION_MODEL_KEY, uploadData.model || 'unknown');
	sessionStorage.setItem(LATEST_DESCRIPTION_KEY, questionDescription);

	latestVideoRequestPayload = {
		explanation,
		questionDescription,
		graphUrl: uploadData.graph_url || '',
	};

	setGenerateVideoButtonState(Boolean(explanation && questionDescription));
	setVideoStatus('Explanation ready. Click "Generate Video Explanation".');

	if (questionDescription) {
		return;
	}

	setVideoStatus('Description missing for video generation. Please try upload again.');
}

if (generateVideoButton) {
	generateVideoButton.addEventListener('click', () => {
		requestAndLoadVideo();
	});
}

async function ensureAuthenticated() {
	try {
		const response = await fetch(AUTH_ME_URL, { credentials: 'include' });
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
			await fetch(AUTH_LOGOUT_URL, { method: 'POST', credentials: 'include' });
		} finally {
			window.location.href = LOGIN_PAGE_URL;
		}
	});
}

ensureAuthenticated().then((isAuthed) => {
	if (isAuthed) {
		runBackendPipeline();
	}
});
