(function () {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta || !meta.content) {
        return;
    }

    const token = meta.content;
    window.csrfToken = token;

    const unsafeMethod = /^(POST|PUT|PATCH|DELETE)$/i;

    function requestMethod(input, options) {
        if (options.method) {
            return options.method;
        }
        if (input && typeof input !== 'string' && input.method) {
            return input.method;
        }
        return 'GET';
    }

    const originalFetch = window.fetch;
    window.fetch = function (input, init) {
        const options = init ? Object.assign({}, init) : {};
        if (unsafeMethod.test(requestMethod(input, options))) {
            const headers = new Headers(options.headers || {});
            if (!headers.has('X-CSRFToken') && !headers.has('X-CSRF-Token')) {
                headers.set('X-CSRFToken', token);
            }
            options.headers = headers;
        }
        return originalFetch.call(this, input, options);
    };

    if (window.jQuery) {
        window.jQuery(document).ajaxSend(function (event, xhr, settings) {
            const method = settings.type || settings.method || 'GET';
            if (unsafeMethod.test(method)) {
                xhr.setRequestHeader('X-CSRFToken', token);
            }
        });
    }
})();
