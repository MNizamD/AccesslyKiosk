let winApi = null;

async function initialize() {
    // Set PC name in the login wall
    winApi = await waitForPyWebview();
    if (winApi) {
        const pcName = await winApi.get_pc_name();
        document.getElementById("pc-name").innerText = pcName;
    } else {
        location.reload(true);
    }

    await fadeOut("loading-screen");
}

initialize();
function login() {
    login_input = document.getElementById("id_input");
    // if (login_input.value === "try") {
    //     if(isInPyWebview()) winApi.close_wall();
    //     login_input.value = "";
    //     return;
    // }
    if (winApi)
        winApi.validate_login(login_input.value);
    
    login_input.value = "";
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();
        login();
    }
});

const input = document.getElementById("id_input");
input.addEventListener("input", () => {
    // If the input contains anything not a number
    if (/[^0-9]/.test(input.value)) {
        input.type = "password";
    } else {
        input.type = "text";
    }
});
