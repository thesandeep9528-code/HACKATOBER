// Chatbot Logic
const chatbotToggle = document.getElementById('chatbot-toggle');
const chatbotWindow = document.getElementById('chatbot-window');
const chatbotCloseBtn = document.getElementById('chatbot-close-btn');
const chatbotIcon = document.getElementById('chatbot-icon');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');
const chatMessages = document.getElementById('chat-messages');
const faqToggle = document.getElementById('faq-toggle');
const faqBrowser = document.getElementById('faq-browser');
const faqSearch = document.getElementById('faq-search');
const faqList = document.getElementById('faq-list');
const voiceInputButton = document.getElementById('chat-voice-input');
const voiceOutputButton = document.getElementById('chat-voice-output');
const voiceStatus = document.getElementById('chat-voice-status');

let isOpen = false;
let chatbotFaqs = [];
let isListening = false;
let voiceOutputEnabled = true;
let serverTranscriptionEnabled = false;
let mediaRecorder = null;
let mediaStream = null;
let recordedAudioChunks = [];

const languageLocales = {
    en: 'en-IN',
    hi: 'hi-IN',
    te: 'te-IN',
    ta: 'ta-IN',
    kn: 'kn-IN',
    ml: 'ml-IN',
    bn: 'bn-IN'
};

function getSelectedLanguage() {
    const translationCookie = document.cookie.match(/(?:^|;\s*)googtrans=([^;]+)/);
    const cookieParts = translationCookie
        ? decodeURIComponent(translationCookie[1]).split('/').filter(Boolean)
        : [];
    const cookieLanguage = cookieParts.length ? cookieParts[cookieParts.length - 1] : '';
    const savedLanguage = cookieLanguage || window.localStorage.getItem('agrismart-language');
    const pageLanguage = document.documentElement.lang.split('-')[0];
    const language = savedLanguage || pageLanguage || 'en';
    const selectedLanguage = languageLocales[language] ? language : 'en';
    document.documentElement.lang = selectedLanguage;
    return selectedLanguage;
}

function getSelectedLocale() {
    return languageLocales[getSelectedLanguage()];
}

function setVoiceStatus(message) {
    if (voiceStatus) voiceStatus.textContent = message;
}

function getSpeechRecognitionConstructor() {
    return window.SpeechRecognition || window.webkitSpeechRecognition;
}

const SpeechRecognition = getSpeechRecognitionConstructor();
const speechRecognition = SpeechRecognition ? new SpeechRecognition() : null;

const speechCapabilitiesPromise = fetch('/chatbot/speech-capabilities')
    .then((response) => {
        if (!response.ok) throw new Error(`Speech capability request failed with status ${response.status}`);
        return response.json();
    })
    .then((capabilities) => {
        serverTranscriptionEnabled = capabilities.server_transcription === true;
        return serverTranscriptionEnabled;
    })
    .catch((error) => {
        console.error('Could not check server speech transcription:', error);
        return false;
    });

if (speechRecognition) {
    speechRecognition.continuous = false;
    speechRecognition.interimResults = false;
    speechRecognition.onstart = () => {
        isListening = true;
        voiceInputButton?.classList.add('is-listening');
        voiceInputButton?.setAttribute('aria-label', 'Stop voice input');
        voiceInputButton.title = 'Stop voice input';
        setVoiceStatus('Listening… speak your question.');
    };
    speechRecognition.onresult = (event) => {
        const transcript = event.results[event.resultIndex][0].transcript.trim();
        if (!transcript) return;
        chatInput.value = transcript;
        setVoiceStatus(`You said: ${transcript}`);
        handleSend();
    };
    speechRecognition.onerror = (event) => {
        const messages = {
            'not-allowed': 'Allow microphone access in your browser to use voice input.',
            'service-not-allowed': 'Voice recognition is unavailable. Check your browser settings.',
            'no-speech': 'No speech detected. Tap the microphone and try again.',
            'network': 'Browser voice recognition failed. Check the local app connection or type your question.'
        };
        setVoiceStatus(messages[event.error] || 'Voice input failed. Please try again.');
    };
    speechRecognition.onend = () => {
        isListening = false;
        voiceInputButton?.classList.remove('is-listening');
        voiceInputButton?.setAttribute('aria-label', 'Ask by voice');
        if (voiceInputButton) voiceInputButton.title = 'Ask by voice';
    };
} else if (voiceInputButton) {
    voiceInputButton.title = 'Ask by voice using local speech recognition.';
    voiceInputButton.setAttribute('aria-label', 'Ask by voice');
}

async function translateReply(text, targetLanguage) {
    const parameters = new URLSearchParams({
        client: 'gtx',
        sl: 'auto',
        tl: targetLanguage,
        dt: 't',
        q: text
    });
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 10000);
    try {
        const response = await fetch(`https://translate.googleapis.com/translate_a/single?${parameters}`, {
            signal: controller.signal
        });
        if (!response.ok) {
            throw new Error(`Reply translation failed with status ${response.status}`);
        }

        const result = await response.json();
        const translatedText = Array.isArray(result?.[0])
            ? result[0].map((segment) => Array.isArray(segment) ? segment[0] : '').join('').trim()
            : '';
        if (!translatedText) {
            throw new Error('Reply translation returned no text');
        }
        return translatedText;
    } finally {
        window.clearTimeout(timeout);
    }
}

async function speakReply(bubble, originalText) {
    if (!voiceOutputEnabled || !window.speechSynthesis || !bubble) return;

    const language = getSelectedLanguage();
    let spokenText = originalText;
    if (language !== 'en') {
        setVoiceStatus('Translating spoken reply…');
        try {
            spokenText = await translateReply(originalText, language);
        } catch (error) {
            console.error('Could not translate spoken reply:', error);
            setVoiceStatus('Could not translate the reply for voice. Check your internet connection and try again.');
            return;
        }
    }
    if (!voiceOutputEnabled || !spokenText) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(spokenText);
    utterance.lang = languageLocales[language];
    const voices = window.speechSynthesis.getVoices();
    utterance.voice = voices.find((voice) =>
        voice.lang.toLowerCase().startsWith(language.toLowerCase())
    ) || null;
    utterance.onerror = (event) => {
        if (event.error !== 'canceled' && event.error !== 'interrupted') {
            setVoiceStatus('Spoken replies are unavailable in this browser.');
        }
    };
    window.speechSynthesis.speak(utterance);
}

async function releaseMediaStream() {
    if (mediaStream) {
        mediaStream.getTracks().forEach((track) => track.stop());
        mediaStream = null;
    }
}

async function transcribeRecording(blob) {
    if (!blob.size) {
        setVoiceStatus('The recording was empty. Tap the microphone and try again.');
        return;
    }

    setVoiceStatus('Transcribing locally… First use may download the speech model (~460 MB).');
    const formData = new FormData();
    const extension = blob.type.includes('mp4') ? 'm4a' : blob.type.includes('ogg') ? 'ogg' : 'webm';
    formData.append('audio', blob, `farmer-question.${extension}`);
    formData.append('language', getSelectedLanguage());

    try {
        const response = await fetch('/chatbot/transcribe', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || `Transcription failed with status ${response.status}`);
        }

        chatInput.value = result.text;
        setVoiceStatus(`You said: ${result.text}`);
        await handleSend(result.text);
    } catch (error) {
        console.error('Could not transcribe voice recording:', error);
        setVoiceStatus(error.message || 'Could not transcribe the recording. Please try again.');
    }
}

async function startServerRecording() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setVoiceStatus('Audio recording is not supported in this browser. Type your question instead.');
        return;
    }

    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const preferredTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'];
        const mimeType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type));
        mediaRecorder = mimeType
            ? new MediaRecorder(mediaStream, { mimeType })
            : new MediaRecorder(mediaStream);
        recordedAudioChunks = [];
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size) recordedAudioChunks.push(event.data);
        };
        mediaRecorder.onerror = (event) => {
            console.error('Audio recording failed:', event.error);
            setVoiceStatus('Could not record audio. Check microphone access and try again.');
            void releaseMediaStream();
        };
        mediaRecorder.onstop = async () => {
            const recording = new Blob(recordedAudioChunks, {
                type: mediaRecorder.mimeType || 'audio/webm'
            });
            recordedAudioChunks = [];
            await releaseMediaStream();
            await transcribeRecording(recording);
        };
        mediaRecorder.start();
        isListening = true;
        voiceInputButton.classList.add('is-listening');
        voiceInputButton.setAttribute('aria-label', 'Stop recording');
        voiceInputButton.title = 'Stop recording';
        setVoiceStatus('Listening… tap the microphone again when you are done.');
    } catch (error) {
        console.error('Could not start server voice recording:', error);
        await releaseMediaStream();
        setVoiceStatus(error.name === 'NotAllowedError'
            ? 'Allow microphone access in your browser to use voice input.'
            : 'Could not start recording. Check microphone access and try again.');
    }
}

voiceInputButton?.addEventListener('click', async () => {
    window.speechSynthesis?.cancel();
    setVoiceStatus('');

    const serverAvailable = await speechCapabilitiesPromise;
    if (isListening) {
        if (mediaRecorder?.state === 'recording') {
            mediaRecorder.stop();
        } else {
            speechRecognition?.stop();
        }
        isListening = false;
        voiceInputButton.classList.remove('is-listening');
        voiceInputButton.setAttribute('aria-label', 'Ask by voice');
        voiceInputButton.title = 'Ask by voice';
        return;
    }

    if (serverAvailable) {
        await startServerRecording();
        return;
    }

    if (!speechRecognition) {
        setVoiceStatus('Local transcription is unavailable. Restart the app after installing its requirements, or type your question.');
        return;
    }

    speechRecognition.lang = getSelectedLocale();
    try {
        speechRecognition.start();
    } catch (error) {
        console.error('Could not start voice recognition:', error);
        setVoiceStatus('Could not start voice input. Please try again.');
    }
});

voiceOutputButton?.addEventListener('click', () => {
    voiceOutputEnabled = !voiceOutputEnabled;
    voiceOutputButton.setAttribute('aria-pressed', String(voiceOutputEnabled));
    voiceOutputButton.setAttribute(
        'aria-label',
        voiceOutputEnabled ? 'Mute spoken replies' : 'Enable spoken replies'
    );
    voiceOutputButton.title = voiceOutputEnabled ? 'Mute spoken replies' : 'Enable spoken replies';
    voiceOutputButton.innerHTML = voiceOutputEnabled
        ? '<i data-lucide="volume-2" class="w-4 h-4"></i>'
        : '<i data-lucide="volume-x" class="w-4 h-4"></i>';
    if (!voiceOutputEnabled) window.speechSynthesis?.cancel();
    if (typeof lucide !== 'undefined') lucide.createIcons();
});

function renderFaqs(searchTerm = '') {
    if (!faqList) return;

    const normalizedSearch = searchTerm.trim().toLowerCase();
    const filteredFaqs = chatbotFaqs.filter((faq) =>
        !normalizedSearch ||
        faq.question.toLowerCase().includes(normalizedSearch) ||
        faq.category.toLowerCase().includes(normalizedSearch)
    );

    faqList.replaceChildren();
    if (!filteredFaqs.length) {
        const emptyMessage = document.createElement('p');
        emptyMessage.className = 'chatbot-faq-empty';
        emptyMessage.textContent = chatbotFaqs.length
            ? 'No matching questions. Try another search.'
            : 'FAQs could not be loaded. Please try again later.';
        faqList.appendChild(emptyMessage);
        return;
    }

    filteredFaqs.forEach((faq) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'chatbot-faq-item';
        button.textContent = faq.question;
        button.dataset.faqQuestion = faq.question;
        faqList.appendChild(button);
    });
}

async function loadChatbotFaqs() {
    try {
        const response = await fetch('/chatbot/faqs');
        if (!response.ok) {
            throw new Error(`FAQ request failed with status ${response.status}`);
        }

        const faqs = await response.json();
        if (!Array.isArray(faqs)) {
            throw new Error('FAQ response was not a list');
        }
        chatbotFaqs = faqs;
        renderFaqs(faqSearch?.value || '');
    } catch (error) {
        console.error('Could not load chatbot FAQs:', error);
        renderFaqs(faqSearch?.value || '');
    }
}

function openChatbot() {
    isOpen = true;
    chatbotWindow.classList.remove('hidden');
    chatbotWindow.classList.add('flex');
    chatbotToggle.classList.add('is-open');
    chatbotToggle.setAttribute('aria-label', 'Close AI farming assistant');
    chatbotToggle.title = 'Close AI farming assistant';
    chatbotIcon.innerHTML = `<i data-lucide="x" class="w-6 h-6"></i>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    chatInput?.focus();
}

function closeChatbot() {
    if (mediaRecorder?.state === 'recording') {
        mediaRecorder.onstop = null;
        mediaRecorder.stop();
        void releaseMediaStream();
        isListening = false;
        voiceInputButton?.classList.remove('is-listening');
    }
    if (isListening) speechRecognition?.stop();
    isOpen = false;
    chatbotWindow.classList.remove('flex');
    chatbotWindow.classList.add('hidden');
    chatbotToggle.classList.remove('is-open');
    chatbotToggle.setAttribute('aria-label', 'Open AI farming assistant');
    chatbotToggle.title = 'Open AI farming assistant';
    chatbotIcon.innerHTML = `<i data-lucide="bot" class="w-7 h-7"></i>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Toggle Chatbot Window
chatbotToggle?.addEventListener('click', () => {
    if (isOpen) {
        closeChatbot();
    } else {
        openChatbot();
    }
});

chatbotCloseBtn?.addEventListener('click', () => {
    closeChatbot();
});

faqToggle?.addEventListener('click', () => {
    const isExpanded = faqToggle.getAttribute('aria-expanded') === 'true';
    faqToggle.setAttribute('aria-expanded', String(!isExpanded));
    faqBrowser?.classList.toggle('hidden', isExpanded);
    if (!isExpanded) faqSearch?.focus();
});

faqSearch?.addEventListener('input', () => {
    renderFaqs(faqSearch.value);
});

faqList?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-faq-question]');
    if (!button || !chatInput) return;

    chatInput.value = button.dataset.faqQuestion;
    faqBrowser?.classList.add('hidden');
    faqToggle?.setAttribute('aria-expanded', 'false');
    handleSend();
});

// Append Message to UI
function appendMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `flex items-end gap-2 max-w-full min-w-0 ${type === 'user' ? 'justify-end' : 'justify-start'}`;

    if (type === 'user') {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble-content bg-primary text-white p-3 rounded-2xl rounded-br-none max-w-[85%] text-sm leading-relaxed shadow-sm min-w-0 break-words';
        bubble.innerHTML = text;
        msgDiv.appendChild(bubble);
    } else {
        const iconDiv = document.createElement('div');
        iconDiv.className = 'w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0';
        iconDiv.innerHTML = '<i data-lucide="bot" class="w-3.5 h-3.5 text-emerald-600"></i>';

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble-content bg-white border border-gray-100 shadow-sm p-3 rounded-2xl rounded-bl-none max-w-[85%] text-sm text-gray-700 leading-relaxed min-w-0 break-words';
        bubble.innerHTML = text;

        msgDiv.appendChild(iconDiv);
        msgDiv.appendChild(bubble);
    }

    chatMessages.appendChild(msgDiv);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return type === 'bot' ? msgDiv.querySelector('.chat-bubble-content') : null;
}

// Show Typing Indicator
function showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.id = 'bot-typing-indicator';
    indicatorDiv.className = 'flex items-end gap-2 justify-start max-w-full min-w-0';
    indicatorDiv.innerHTML = `
        <div class="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <i data-lucide="bot" class="w-3.5 h-3.5 text-emerald-600"></i>
        </div>
        <div class="bg-white border border-gray-100 shadow-sm px-4 py-3 rounded-2xl rounded-bl-none max-w-[85%] text-sm text-gray-400 flex items-center gap-1.5">
            <span class="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></span>
            <span class="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
            <span class="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.4s]"></span>
        </div>
    `;
    chatMessages.appendChild(indicatorDiv);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide Typing Indicator
function hideTypingIndicator() {
    const indicator = document.getElementById('bot-typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Send Message Logic
async function handleSend(questionOverride = '') {
    const questionText = (questionOverride || chatInput.value).trim();
    if (!questionText) return;

    // Add User Message (escaped plain text)
    const userMessageDiv = document.createElement('div');
    userMessageDiv.textContent = questionText;
    appendMessage(userMessageDiv.innerHTML, 'user');
    chatInput.value = '';

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Show Typing Indicator
    showTypingIndicator();

    try {
        // Fetch response from chatbot endpoint
        const response = await fetch('/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: questionText })
        });

        hideTypingIndicator();

        if (response.ok) {
            const data = await response.json();
            const rawMarkdown = data.response || "No response received.";
            let safeHTML = rawMarkdown;
            if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
                safeHTML = marked.parse(rawMarkdown);
            }
            if (typeof DOMPurify !== 'undefined') {
                safeHTML = DOMPurify.sanitize(safeHTML);
            }

            // Add Bot Reply
            const replyBubble = appendMessage(safeHTML, 'bot');
            speakReply(replyBubble, replyBubble?.textContent.trim() || rawMarkdown);
        } else {
            appendMessage("Sorry, there seems to be a problem reaching BioGrow AI. Please try again.", "bot");
        }
    } catch (err) {
        hideTypingIndicator();
        appendMessage("Network connection error. Please check your connection and try again.", "bot");
    }

    // Scroll to Bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Event Listeners for Sending
chatSend?.addEventListener('click', handleSend);
chatInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});

loadChatbotFaqs();
if (typeof lucide !== 'undefined') lucide.createIcons();
