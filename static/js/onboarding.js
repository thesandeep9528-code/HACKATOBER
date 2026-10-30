(function () {
    const userId = document.body.dataset.tourUser;
    if (!userId) return;

    const supportedLanguages = {
        en: 'English',
        hi: 'हिन्दी',
        te: 'తెలుగు',
        ta: 'தமிழ்',
        kn: 'ಕನ್ನಡ',
        ml: 'മലയാളം',
        bn: 'বাংলা'
    };
    const completionKey = `agrismart-tour-completed-v2:${userId}`;
    const translatorCache = new Map();
    const params = new URLSearchParams(window.location.search);
    const restartTour = params.get('restart_tour') === '1';
    if (restartTour) {
        params.delete('restart_tour');
        const query = params.toString();
        const cleanUrl = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`;
        window.history.replaceState(window.history.state, '', cleanUrl);
    }
    const tourLanguage = params.get('lang');
    let language = Object.hasOwn(supportedLanguages, tourLanguage)
        ? tourLanguage
        : window.localStorage.getItem('agrismart-language') || 'en';
    if (!Object.hasOwn(supportedLanguages, language)) language = 'en';

    const backdrop = document.createElement('div');
    backdrop.className = 'onboarding-backdrop notranslate';
    backdrop.setAttribute('aria-hidden', 'true');
    const spotlight = document.createElement('div');
    spotlight.className = 'onboarding-spotlight notranslate';
    spotlight.setAttribute('aria-hidden', 'true');
    const finger = document.createElement('div');
    finger.className = 'onboarding-finger notranslate';
    finger.textContent = '👆';
    finger.setAttribute('aria-hidden', 'true');
    const card = document.createElement('section');
    card.className = 'onboarding-card notranslate';
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-labelledby', 'onboarding-title');
    card.setAttribute('aria-describedby', 'onboarding-description');

    let mode = '';
    let activeStep = 0;
    let dismissed = false;
    let statusText = '';

    const dashboardSteps = [
        { target: 'welcome', title: 'Your farm at a glance', description: 'Start here for your welcome, local weather, and a quick overview of your farming workspace.' },
        { target: 'diagnostic', title: 'Check a crop leaf', description: 'Open Leaf Diagnostic to check a clear crop-leaf photo and explore the crop-focus options.' },
        { target: 'irrigation', title: 'Plan irrigation', description: 'Use measured field conditions and the growth-stage menu to understand the irrigation recommendation.' },
        { target: 'crop-advisory', title: 'Find a crop recommendation', description: 'Use soil-test nutrients, pH, humidity, temperature, and the soil-type dropdown to explore a crop recommendation.' },
        { target: 'field-logs', title: 'Keep field records', description: 'Choose a farm and record observations such as soil moisture, leaf color, and crop growth.' },
        { target: 'community', title: 'Learn with other farmers', description: 'Visit Community in the main menu (or open the menu on your phone) to ask questions and share experience.' },
        { target: 'chatbot', title: 'Ask your farming assistant', description: 'Open the AI Farming Assistant for crop questions, searchable FAQs, and voice input.' }
    ];

    const services = [
        { id: 'crop', title: 'Smart Crop Advisory', route: '/crop_prediction', description: 'Practice entering N-P-K values, pH, climate measurements, and selecting a soil type.' },
        { id: 'irrigation', title: 'Irrigation Advisory', route: '/disease_detection#irrigation-advisory', description: 'Practice choosing a crop growth stage and entering moisture, temperature, and rainfall values.' },
        { id: 'diagnostic', title: 'Leaf Diagnostics', route: '/disease_detection#leaf-diagnostic', description: 'Learn crop focus and image upload steps before running a real diagnosis.' }
    ];

    const serviceSteps = {
        crop: [
            { target: 'crop-n', title: 'Nitrogen (N)', description: 'Enter the soil-test nitrogen result in kg/ha. The form accepts 0 to 300. For this demonstration, try 90.', selector: '#nitrogen', value: '90' },
            { target: 'crop-p', title: 'Phosphorus (P)', description: 'Enter phosphorus from your soil test in kg/ha. Example value: 42.', selector: '#phosphorus', value: '42' },
            { target: 'crop-k', title: 'Potassium (K)', description: 'Enter potassium from your soil test in kg/ha. Example value: 43.', selector: '#potassium', value: '43' },
            { target: 'crop-ph', title: 'Soil pH', description: 'Enter the pH from your soil test, between 0 and 14. The example 6.5 is mildly acidic.', selector: '#ph', value: '6.5' },
            { target: 'crop-humidity', title: 'Average humidity', description: 'Enter average local humidity as a percentage from 0 to 100. Example: 80%.', selector: '#humidity', value: '80' },
            { target: 'crop-temperature', title: 'Average temperature', description: 'Enter the average temperature in degrees Celsius. Example: 25°C.', selector: '#temperature', value: '25' },
            { target: 'crop-soil', title: 'Choose the soil type', description: 'Open this dropdown and select the soil classification that best matches your field. For practice, use Alluvial Soil.', selector: '#soil', value: 'Alluvial Soil' },
            { target: 'crop-soil', title: 'Review before recommendation', description: 'Check every value against your own soil test and local climate. These are sample values only. Select Get ML Recommendation when you are ready; this tour will not submit the form.' }
        ],
        irrigation: [
            { target: 'irrigation-crop', title: 'Target crop', description: 'Enter the crop in the field. This example uses Tomato; replace it with the crop growing in your field.', selector: '[name="crop"]', value: 'Tomato' },
            { target: 'irrigation-stage', title: 'Choose growth stage', description: 'Open the dropdown and choose the crop’s current stage. Growing is selected in this example; stages include Vegetative, Flowering, Growing, and Ripening.', selector: '[name="stage"]', value: 'growing' },
            { target: 'irrigation-moisture', title: 'Soil moisture', description: 'Enter a soil moisture percentage from 0 to 100. Example: 32%. Use a field reading if available.', selector: '[name="soil_moisture_pct"]', value: '32' },
            { target: 'irrigation-temperature', title: 'Temperature', description: 'Enter the current field temperature in degrees Celsius. Example: 30°C.', selector: '[name="temperature_c"]', value: '30' },
            { target: 'irrigation-humidity', title: 'Humidity', description: 'Enter relative humidity as a percentage from 0 to 100. Example: 65%.', selector: '[name="humidity_pct"]', value: '65' },
            { target: 'irrigation-rain-mm', title: 'Forecast rainfall', description: 'Enter expected rainfall in millimeters. Example: 5 mm. Use the forecast for your area.', selector: '[name="forecast_rain_mm"]', value: '5' },
            { target: 'irrigation-rain-probability', title: 'Rain probability', description: 'Enter the chance of rain as a percentage from 0 to 100. Example: 70%.', selector: '[name="rain_probability_pct"]', value: '70' },
            { target: 'irrigation-rain-probability', title: 'Review irrigation inputs', description: 'The example set is Tomato, Growing, 32% moisture, 30°C, 65% humidity, 5 mm forecast rain, and 70% rain probability. Replace every sample with actual local readings. The tour will not calculate or submit.' }
        ],
        diagnostic: [
            { target: 'diagnostic-crop', title: 'Choose a crop focus', description: 'The crop pills help focus the scanner when you know the crop. Choose Tomato, Potato, Corn, Apple, or keep Auto-Detect. For this demonstration, select Tomato.', selector: '[data-crop="tomato"]', action: 'click' },
            { target: 'diagnostic-upload', title: 'Choose a clear leaf photo', description: 'Click or drag a PNG or JPG image of one crop leaf into this area. Use a sharp, well-lit photo with visible symptoms. The tour does not upload an image.' },
            { target: 'diagnostic-upload', title: 'Run a diagnosis when ready', description: 'After selecting your own image, choose Analyze Foliage. Check the result carefully and consult a local agriculture expert before treatment. This tour will not start a diagnosis.' }
        ]
    };

    function setLanguage(nextLanguage) {
        if (!Object.hasOwn(supportedLanguages, nextLanguage)) return;
        language = nextLanguage;
        window.localStorage.setItem('agrismart-language', language);
        document.documentElement.lang = language;
        document.cookie = `googtrans=/en/${language}; path=/; SameSite=Lax`;
        document.cookie = `googtrans=/en/${language}; path=/; domain=${window.location.hostname}; SameSite=Lax`;
        const googleSelect = document.querySelector('#google_translate_element select.goog-te-combo');
        if (googleSelect) {
            googleSelect.value = language === 'en' ? '' : language;
            googleSelect.dispatchEvent(new Event('change'));
        }
    }

    async function translate(text) {
        if (language === 'en' || !text) return text;
        const cacheKey = `${language}:${text}`;
        if (translatorCache.has(cacheKey)) return translatorCache.get(cacheKey);
        const query = new URLSearchParams({ client: 'gtx', sl: 'en', tl: language, dt: 't', q: text });
        const response = await fetch(`https://translate.googleapis.com/translate_a/single?${query}`);
        if (!response.ok) throw new Error(`Tour translation failed with status ${response.status}`);
        const result = await response.json();
        const translated = Array.isArray(result?.[0])
            ? result[0].map((part) => Array.isArray(part) ? part[0] : '').join('').trim()
            : '';
        if (!translated) throw new Error('Tour translation returned no text');
        translatorCache.set(cacheKey, translated);
        return translated;
    }

    async function translated(text) {
        try {
            return await translate(text);
        } catch (error) {
            console.error('Could not translate onboarding text:', error);
            statusText = 'Tour translation is unavailable. Check your internet connection, then try again or choose English.';
            throw error;
        }
    }

    function finishTour() {
        try {
            window.localStorage.setItem(completionKey, 'true');
        } catch (error) {
            console.error('Could not save onboarding completion:', error);
        }
        closeTour();
    }

    function closeTour() {
        if (dismissed) return;
        dismissed = true;
        window.removeEventListener('resize', positionTour);
        window.removeEventListener('scroll', positionTour, true);
        document.removeEventListener('keydown', onKeyDown);
        backdrop.remove();
        spotlight.remove();
        finger.remove();
        card.remove();
    }

    function getVisibleTarget(targetName) {
        return Array.from(document.querySelectorAll(`[data-tour-target="${targetName}"]`))
            .find((element) => element.getBoundingClientRect().width > 0);
    }

    function positionTour() {
        if (dismissed) return;
        if (mode === 'language' || mode === 'services') {
            spotlight.hidden = true;
            finger.hidden = true;
            card.style.left = `${Math.max(16, (window.innerWidth - 390) / 2)}px`;
            card.style.top = `${Math.max(16, (window.innerHeight - card.offsetHeight) / 2)}px`;
            return;
        }

        const steps = mode === 'dashboard' ? dashboardSteps : serviceSteps[mode];
        const target = getVisibleTarget(steps[activeStep]?.target);
        if (!target) {
            spotlight.hidden = true;
            finger.hidden = true;
            card.style.left = `${Math.max(16, (window.innerWidth - 390) / 2)}px`;
            card.style.top = `${Math.max(16, (window.innerHeight - card.offsetHeight) / 2)}px`;
            return;
        }

        spotlight.hidden = false;
        finger.hidden = false;
        let rect = target.getBoundingClientRect();
        if (rect.top < 12 || rect.bottom > window.innerHeight - 12) {
            target.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
            rect = target.getBoundingClientRect();
        }
        const padding = 7;
        const left = Math.max(6, rect.left - padding);
        const top = Math.max(6, rect.top - padding);
        spotlight.style.left = `${left}px`;
        spotlight.style.top = `${top}px`;
        spotlight.style.width = `${Math.min(window.innerWidth - left - 6, rect.width + padding * 2)}px`;
        spotlight.style.height = `${Math.min(window.innerHeight - top - 6, rect.height + padding * 2)}px`;
        finger.style.left = `${Math.min(window.innerWidth - 48, rect.right - 32)}px`;
        finger.style.top = `${Math.max(8, rect.top - 42)}px`;

        const cardWidth = Math.min(390, window.innerWidth - 32);
        const cardHeight = card.offsetHeight;
        const cardLeft = Math.min(
            window.innerWidth - cardWidth - 16,
            Math.max(16, rect.left + rect.width / 2 - cardWidth / 2)
        );
        const below = rect.bottom + 18;
        const above = rect.top - cardHeight - 18;
        const cardTop = below + cardHeight <= window.innerHeight - 16
            ? below
            : above >= 16
                ? above
                : Math.max(16, window.innerHeight - cardHeight - 16);
        card.style.left = `${cardLeft}px`;
        card.style.top = `${cardTop}px`;
    }

    function createButton(label, className, action) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = className;
        button.textContent = label;
        button.addEventListener('click', action);
        return button;
    }

    function showLanguagePicker() {
        mode = 'language';
        card.replaceChildren();
        const heading = document.createElement('h2');
        heading.id = 'onboarding-title';
        heading.textContent = 'Choose your learning language';
        const description = document.createElement('p');
        description.id = 'onboarding-description';
        description.textContent = 'Select the language you are most comfortable reading. The guided lessons and examples will use your choice.';
        const select = document.createElement('select');
        select.className = 'onboarding-language-select';
        select.setAttribute('aria-label', 'Learning language');
        Object.entries(supportedLanguages).forEach(([code, nativeName]) => {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = nativeName;
            select.appendChild(option);
        });
        select.value = language;
        const status = document.createElement('p');
        status.className = 'onboarding-error';
        status.setAttribute('role', 'status');
        status.setAttribute('aria-live', 'polite');
        const actions = document.createElement('div');
        actions.className = 'onboarding-card-actions';
        const skip = createButton('Skip learning', 'onboarding-skip', finishTour);
        const start = createButton('Start learning', 'onboarding-next', async () => {
            setLanguage(select.value);
            start.disabled = true;
            status.textContent = '';
            try {
                await renderDashboardStep();
            } catch (error) {
                status.textContent = statusText;
                start.disabled = false;
            }
        });
        let selectionRevision = 0;
        async function updateLanguagePicker() {
            const revision = ++selectionRevision;
            setLanguage(select.value);
            start.disabled = true;
            status.textContent = '';
            try {
                const [translatedHeading, translatedDescription, translatedStart, translatedSkip] = await Promise.all([
                    translated('Choose your learning language'),
                    translated('Select the language you are most comfortable reading. The guided lessons and examples will use your choice.'),
                    translated('Start learning'),
                    translated('Skip learning')
                ]);
                if (revision !== selectionRevision || select.value !== language) return;
                heading.textContent = translatedHeading;
                description.textContent = translatedDescription;
                start.textContent = translatedStart;
                skip.textContent = translatedSkip;
            } catch (error) {
                console.error('Could not translate the language picker:', error);
                status.textContent = statusText;
            } finally {
                if (revision === selectionRevision) start.disabled = false;
            }
        }
        select.addEventListener('change', () => void updateLanguagePicker());
        actions.append(skip, start);
        card.append(heading, description, select, status, actions);
        positionTour();
        if (language !== 'en') void updateLanguagePicker();
    }

    async function renderDashboardStep() {
        mode = 'dashboard';
        if (activeStep >= dashboardSteps.length) {
            await showServices();
            return;
        }
        const step = dashboardSteps[activeStep];
        await renderLesson({
            label: `Explore your farm · ${activeStep + 1} of ${dashboardSteps.length}`,
            title: step.title,
            description: step.description,
            nextLabel: activeStep + 1 === dashboardSteps.length ? 'Explore services' : 'Next',
            onNext: async () => {
                activeStep += 1;
                await renderDashboardStep();
            }
        });
    }

    async function showServices() {
        mode = 'services';
        const title = await translated('Practice with guided examples');
        const description = await translated('Go deeper: open a service lesson to see which dropdowns to choose and how to enter sample numbers. Sample values are for practice only.');
        const skipLabel = await translated('Skip learning');
        const finishLabel = await translated('Finish learning');
        card.replaceChildren();
        const label = document.createElement('div');
        label.className = 'onboarding-card-label';
        label.textContent = await translated('Hands-on service lessons');
        const heading = document.createElement('h2');
        heading.id = 'onboarding-title';
        heading.textContent = title;
        const intro = document.createElement('p');
        intro.id = 'onboarding-description';
        intro.textContent = description;
        const list = document.createElement('div');
        list.className = 'onboarding-service-list';
        for (const service of services) {
            const link = document.createElement('a');
            link.className = 'onboarding-service-link';
            const route = new URL(service.route, window.location.origin);
            route.searchParams.set('learn', service.id);
            route.searchParams.set('lang', language);
            link.href = `${route.pathname}${route.search}${route.hash}`;
            const linkTitle = document.createElement('strong');
            linkTitle.textContent = await translated(service.title);
            const linkDescription = document.createElement('span');
            linkDescription.textContent = await translated(service.description);
            link.append(linkTitle, linkDescription);
            list.appendChild(link);
        }
        const actions = document.createElement('div');
        actions.className = 'onboarding-card-actions';
        actions.append(
            createButton(skipLabel, 'onboarding-skip', finishTour),
            createButton(finishLabel, 'onboarding-next', finishTour)
        );
        card.append(label, heading, intro, list, actions);
        positionTour();
        actions.querySelector('.onboarding-next').focus({ preventScroll: true });
    }

    async function renderLesson(content) {
        const [labelText, titleText, descriptionText, nextText, skipText] = await Promise.all([
            translated(content.label),
            translated(content.title),
            translated(content.description),
            translated(content.nextLabel),
            translated('Skip learning')
        ]);
        card.replaceChildren();
        const label = document.createElement('div');
        label.className = 'onboarding-card-label';
        label.textContent = labelText;
        const heading = document.createElement('h2');
        heading.id = 'onboarding-title';
        heading.textContent = titleText;
        const description = document.createElement('p');
        description.id = 'onboarding-description';
        description.textContent = descriptionText;
        const actions = document.createElement('div');
        actions.className = 'onboarding-card-actions';
        actions.appendChild(createButton(skipText, 'onboarding-skip', finishTour));

        if (content.example) {
            const example = document.createElement('div');
            example.className = 'onboarding-demo-value';
            const [exampleLabel, exampleValue, exampleButton] = await Promise.all([
                translated(content.example.label),
                translated(content.example.value),
                translated(content.example.button)
            ]);
            example.textContent = `${exampleLabel}: ${exampleValue}`;
            card.append(label, heading, description, example);
            actions.insertBefore(createButton(exampleButton, 'onboarding-fill', content.example.action), actions.firstChild);
        } else {
            card.append(label, heading, description);
        }
        actions.appendChild(createButton(nextText, 'onboarding-next', async () => {
            try {
                await content.onNext();
            } catch (error) {
                showTranslationFailure();
            }
        }));
        card.appendChild(actions);
        positionTour();
        actions.querySelector('.onboarding-next').focus({ preventScroll: true });
    }

    function showTranslationFailure() {
        const message = document.createElement('p');
        message.className = 'onboarding-error';
        message.setAttribute('role', 'alert');
        message.textContent = statusText;
        card.appendChild(message);
        const englishButton = createButton('Continue in English', 'onboarding-next', () => {
            setLanguage('en');
            statusText = '';
            if (mode === 'dashboard') void renderDashboardStep().catch(showTranslationFailure);
            else if (mode === 'services') void showServices().catch(showTranslationFailure);
            else void renderServiceStep().catch(showTranslationFailure);
        });
        card.appendChild(englishButton);
    }

    function activateIrrigationView() {
        const irrigationView = document.querySelector('#irrigation-advisor-view');
        if (!irrigationView) return;
        document.querySelectorAll('.tool-view').forEach((view) => view.classList.add('hidden'));
        irrigationView.classList.remove('hidden');

        document.querySelectorAll('.tool-tab-btn').forEach((button) => {
            const isIrrigation = button.getAttribute('data-target') === '#irrigation-advisor-view';
            button.classList.toggle('active', isIrrigation);
            button.classList.toggle('bg-white', isIrrigation);
            button.classList.toggle('text-emerald-700', isIrrigation);
            button.classList.toggle('shadow-sm', isIrrigation);
            button.classList.toggle('text-gray-500', !isIrrigation);
        });
    }

    async function renderServiceStep() {
        const steps = serviceSteps[mode];
        if (activeStep >= steps.length) {
            window.location.assign(`/dashboard?tour=services&lang=${language}`);
            return;
        }
        const step = steps[activeStep];
        const title = step.title;
        const description = step.description;
        const label = `Hands-on lesson · ${activeStep + 1} of ${steps.length}`;
        const nextLabel = activeStep + 1 === steps.length ? 'Finish this lesson' : 'Next';
        let example;
        if (step.value !== undefined) {
            example = {
                label: 'Practice value',
                value: step.value,
                button: 'Use example',
                action: () => {
                    const field = document.querySelector(step.selector);
                    if (!field) {
                        statusText = `The example field ${step.selector} is not available on this page.`;
                        showTranslationFailure();
                        return;
                    }
                    field.value = step.value;
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                }
            };
        } else if (step.action === 'click') {
            example = {
                label: 'Practice action',
                value: 'Select Tomato crop focus',
                button: 'Try this choice',
                action: () => {
                    const cropButton = document.querySelector(step.selector);
                    if (!cropButton) {
                        statusText = 'Crop focus controls are unavailable on this page.';
                        showTranslationFailure();
                        return;
                    }
                    try {
                        cropButton.click();
                    } catch (error) {
                        console.error('Could not select the example crop focus:', error);
                        statusText = 'Could not select the example crop focus.';
                        showTranslationFailure();
                    }
                }
            };
        }
        await renderLesson({
            label,
            title,
            description,
            example,
            nextLabel,
            onNext: async () => {
                activeStep += 1;
                await renderServiceStep();
            }
        });
    }

    function onKeyDown(event) {
        if (event.key === 'Escape') finishTour();
    }

    document.body.append(backdrop, spotlight, finger, card);
    window.addEventListener('resize', positionTour);
    window.addEventListener('scroll', positionTour, true);
    document.addEventListener('keydown', onKeyDown);

    if (params.get('learn') && Object.hasOwn(serviceSteps, params.get('learn'))) {
        mode = params.get('learn');
        setLanguage(language);
        if (mode === 'irrigation') {
            activateIrrigationView();
        }
        void renderServiceStep().catch(showTranslationFailure);
    } else if (document.querySelector('[data-tour-dashboard]')) {
        if (params.get('tour') === 'services') {
            setLanguage(language);
            void showServices().catch(showTranslationFailure);
        } else if (restartTour || document.body.dataset.tourNewUser === 'true') {
            showLanguagePicker();
        } else {
            closeTour();
        }
    } else {
        closeTour();
    }
})();
