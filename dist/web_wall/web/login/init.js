let winApi = null;

async function initialize() {
    winApi = await window.getPyWebViewAPI();
    if (winApi) {
        document.getElementById("pc-name").innerText = await winApi.get_pc_name();
    } else {
        fadeOutLoader();
        console.log("Running in browser - initializing mock API");
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            login();
        }
    });
}

initialize();

function login() {
    const login_input = document.getElementById("id_input");
    if (winApi) winApi.validate_login(login_input.value);
    else console.log("You pressed enter!");

    login_input.value = "";
}

const input = document.getElementById("id_input");
input.addEventListener("input", () => {
    // If the input contains anything not a number
    if (/[^0-9]/.test(input.value)) {
        input.type = "password";
    } else {
        input.type = "text";
    }
});
