function waitForPyWebview() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            resolve(window.pywebview.api);
        } else {
            let limit = 5;
            const interval = setInterval(() => {
                if (window.pywebview && window.pywebview.api) {
                    clearInterval(interval);
                    resolve(window.pywebview.api);
                } else {
                    limit -= 1;
                    if (limit < 0) {
                        clearInterval(interval);
                        resolve(null);
                    }
                }
            }, 50); // check every 50ms
        }
    });
}

async function fadeOut(id) {
    return new Promise((resolve) => {
        const element = document.getElementById(id);
        if (!element) return resolve(); // safety check

        element.classList.add("fade-out");

        // Wait for transition to finish before removing
        setTimeout(() => {
            element.remove();
            resolve();
        }, 800); // match your CSS transition duration
    });
}
