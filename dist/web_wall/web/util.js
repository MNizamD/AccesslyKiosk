// function waitForPyWebview() {
//     const pyWebview = new Promise((resolve) => {
//         if (window.pywebview && window.pywebview.api) {
//             resolve(window.pywebview.api);
//         } else {
//             let limit = 5;
//             const interval = setInterval(() => {
//                 if (window.pywebview && window.pywebview.api) {
//                     clearInterval(interval);
//                     resolve(window.pywebview.api);
//                 } else {
//                     limit -= 1;
//                     if (limit < 0) {
//                         clearInterval(interval);
//                         resolve(null);
//                     }
//                 }
//             }, 100); // check every 50ms
//         }
//     });

//     if (!pyWebview){
//         retryPage();
//     } else {
//         return pyWebview
//     }
// }

// async function waitForPyWebview () {
//     let retries = 0;
//     const maxRetries = 5;
//     const delay = 50;

//     while (retries < maxRetries) {
//         if (window.pywebview && window.pywebview.api) {
//             return window.pywebview.api; // success
//         }

//         // wait before next check
//         await new Promise((resolve) => setTimeout(resolve, delay));
//         retries++;
//     }

//     // Max retries reached → optional: retryPage once
//     console.error("PyWebview API not available after retries.");
//     retryPage();
//     return null;
// }

// async function fadeOut(id) {
//     return new Promise((resolve) => {
//         const element = document.getElementById(id);
//         if (!element) return resolve(); // safety check

//         element.classList.add("fade-out");

//         // Wait for transition to finish before removing
//         setTimeout(() => {
//             element.remove();
//             resolve();
//         }, 800); // match your CSS transition duration
//     });
// }

function fadeOutLoader() {
    const element = document.getElementById("loading-screen");
    if (!element) return; // safety check
    element.classList.add("fade-out");
    setTimeout(() => {
        element.remove();
    }, 800);
}

// // function clearAllParams() {
// //     const url = new URL(window.location.href);
// //     url.searchParams.clear();
// //     window.history.replaceState({}, "", url.toString());
// // }

// function retryPage(){
//     const url = new URL(window.location.href);
//     let retry = Number(url.searchParams.get("retry") || "0");
//     if (retry >= 2) {
//             console.error("Stopped reload: reached 3 attempts.");
//             return;  // Stop reloading
//         }

//         // Increment retry counter
//         retry++;
//         url.searchParams.set("retry", retry);

//         // Reload with updated retry count
//         window.location.href = url.toString();
//         return;
// }

window.addEventListener("pywebviewready", function () {
    try {
        // Make API globally available
        window.globalApi = window.pywebview.api;

        // Set a flag
        window.isPyWebViewReady = true;

        // Dispatch custom event for other scripts
        const event = new CustomEvent("pywebview:ready", {
            detail: {
                api: window.pywebview.api,
                timestamp: Date.now(),
            },
        });
        window.dispatchEvent(event);
        console.log("PyWebView API is now globally available as window.globalApi");
        fadeOutLoader();
    } catch (error) {
        console.error("Error initializing PyWebView API:", error);
    }
});

// Safe API access function
window.getPyWebViewAPI = () => {
    return new Promise((resolve) => {
        let tries = 0;
        let limit = 5;
        const interval = setInterval(() => {
            if (window.globalApi) {
                clearInterval(interval);
                resolve(window.globalApi);
            } else {
                tries ++;
                if (tries >= limit) {
                    clearInterval(interval);
                    resolve(null);
                }
            }
        }, 100); // check every 50ms
    });
};
