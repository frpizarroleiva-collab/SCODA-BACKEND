// ===============================
// LOGIN.JS — SCODA
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    // ======================
    // MENSAJES DE LOGIN
    // ======================
    const params = new URLSearchParams(window.location.search);
    const status = params.get("status");
    const msgDiv = document.getElementById("mensaje-login");

    if (status === "logout") {
        msgDiv.innerHTML = '<p class="text-success">Sesión cerrada correctamente.</p>';
    } else if (status === "success") {
        msgDiv.innerHTML = '<p class="text-success">Inicio de sesión exitoso.</p>';
    }

    // ======================
    // MOSTRAR / OCULTAR CONTRASEÑA
    // ======================
    const toggleBtn = document.getElementById("toggle-password");
    const input = document.getElementById("password");

    toggleBtn.addEventListener("click", () => {
        const icon = toggleBtn.querySelector("i");
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        icon.classList.toggle("bi-eye");
        icon.classList.toggle("bi-eye-slash");
    });

    // ======================
    // MODO OSCURO / CLARO
    // ======================
    const currentTheme = localStorage.getItem("theme") || "light";
    document.body.dataset.theme = currentTheme;

    // Crear botón de tema
    const container = document.getElementById("login-container");
    const themeBtn = document.createElement("button");
    themeBtn.id = "toggle-theme";
    themeBtn.className = "btn btn-outline-success position-absolute top-0 end-0 m-3 rounded-circle";
    themeBtn.innerHTML = '<i class="bi bi-moon-fill"></i>';
    themeBtn.title = "Cambiar tema";
    container.appendChild(themeBtn);

    updateThemeIcon(currentTheme);

    themeBtn.addEventListener("click", () => {
        const newTheme = document.body.dataset.theme === "light" ? "dark" : "light";
        document.body.dataset.theme = newTheme;
        localStorage.setItem("theme", newTheme);
        updateThemeIcon(newTheme);
    });

    function updateThemeIcon(theme) {
        const icon = themeBtn.querySelector("i");
        if (theme === "dark") {
            icon.classList.replace("bi-moon-fill", "bi-brightness-high");
            themeBtn.classList.replace("btn-outline-success", "btn-outline-light");
        } else {
            icon.classList.replace("bi-brightness-high", "bi-moon-fill");
            themeBtn.classList.replace("btn-outline-light", "btn-outline-success");
        }
    }
});
