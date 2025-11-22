let winApi = null;

async function initialize() {
    winApi = await window.getPyWebViewAPI();
    if (winApi) {
        document.getElementById("pc-name").innerText = await winApi.get_pc_name();
        details = JSON.parse(await winApi.get_details());
        if (details["version"] && details["updated"]){
            document.getElementById("lbl-version").innerText = details["version"]
            document.getElementById("lbl-updated").innerText = details["updated"]
        }
    } else {
        document.getElementById("btn-refresh").classList.remove("d-none")
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
