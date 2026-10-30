(function () {
    const preferenceKey = "agrismart-language";
    const supportedLanguages = new Set(["en", "hi", "te", "ta", "kn", "ml", "bn"]);

    function getTranslationSelect() {
        return document.querySelector("#google_translate_element select.goog-te-combo");
    }

    function removeTranslateBanner() {
        document.querySelectorAll("body > .skiptranslate").forEach(function (container) {
            if (container.querySelector("iframe.goog-te-banner-frame")) {
                container.remove();
            }
        });

        document.querySelectorAll("iframe.goog-te-banner-frame").forEach(function (frame) {
            frame.remove();
        });
    }

    function watchTranslateBanner() {
        removeTranslateBanner();
        new MutationObserver(removeTranslateBanner).observe(document.documentElement, {
            childList: true,
            subtree: true
        });
    }

    function restoreLanguage(attempt) {
        const select = getTranslationSelect();
        if (!select) {
            const widget = document.querySelector("#google_translate_element .goog-te-gadget-simple a");
            if (widget) {
                widget.setAttribute("aria-label", "Choose website language");
                widget.title = "Choose website language";
                return;
            }
            if (attempt < 50) {
                window.setTimeout(function () {
                    restoreLanguage(attempt + 1);
                }, 100);
            }
            return;
        }

        select.setAttribute("aria-label", "Choose website language");
        select.title = "Choose website language";
        select.addEventListener("change", function () {
            const language = select.value || "en";
            if (supportedLanguages.has(language)) {
                window.localStorage.setItem(preferenceKey, language);
                document.documentElement.lang = language;
            }
        });

        const savedLanguage = window.localStorage.getItem(preferenceKey);
        if (savedLanguage && supportedLanguages.has(savedLanguage)) {
            const targetLanguage = savedLanguage === "en" ? "" : savedLanguage;
            if (select.value !== targetLanguage) {
                select.value = targetLanguage;
                select.dispatchEvent(new Event("change"));
            }
            document.documentElement.lang = savedLanguage;
        }
    }

    window.googleTranslateElementInit = function () {
        watchTranslateBanner();
        new window.google.translate.TranslateElement(
            {
                pageLanguage: "en",
                includedLanguages: "en,hi,te,ta,kn,ml,bn",
                autoDisplay: false,
                layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE
            },
            "google_translate_element"
        );
        restoreLanguage(0);
    };

    const script = document.createElement("script");
    script.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    script.async = true;
    script.onerror = function () {
        const selector = document.getElementById("google_translate_element");
        if (selector) {
            selector.title = "Language translation is unavailable. Check your internet connection.";
        }
        console.error("Could not load the Google Translate language selector.");
    };
    document.head.appendChild(script);
})();
