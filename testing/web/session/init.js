let winSession = null;
let user = null;

async function initialize() {
    // Set User name in the welcome header
    const header = document.getElementById("welcome-header");
    winSession = await waitForPyWebview();
    if (winSession) {
        user = JSON.parse(await winSession.get_user());
        header.innerText = user.name;
    }

    await fadeOut("loading-screen");
}

initialize();

async function logout() {
    if (winSession) {
        // response = await winSession.show_message("Confirm logout?", "Logout", 0x00000004, 0x00000020);
        // if (response != 6) return;
        stopTimer();
        setInterval(async () => await winSession.logout(), 3000);
    } else {
        alert("Logout clicked");
    }
}

let startTime = new Date();
let updateInterval;

function updateDuration() {
    const now = new Date();
    const elapsed = Math.floor((now - startTime) / 1000); // seconds elapsed

    let secs = elapsed % 60;
    let mins = Math.floor(elapsed / 60) % 60;
    let hrs = Math.floor(elapsed / 3600);

    let timeStr;
    if (hrs > 0) {
        timeStr = `${hrs}h ${mins}m ${secs}s`;
    } else if (mins > 0) {
        timeStr = `${mins}m ${secs}s`;
    } else {
        timeStr = `${secs}s`;
    }

    timeLabel = `Logged in: ${timeStr}`;

    // Update label
    document.getElementById("status-timer").innerText = timeLabel;
}

// Start updating once per second
function startTimer() {
    startTime = new Date();
    updateDuration(); // update immediately
    updateInterval = setInterval(updateDuration, 1000);
}

startTimer();

// Stop updating (like logout)
function stopTimer() {
    document.getElementById("status-timer").innerText = "You have successfully logged out!";
    document.getElementById("btn_report").disabled = true;
    document.getElementById("btn_logout").disabled = true;
    clearInterval(updateInterval);
}
