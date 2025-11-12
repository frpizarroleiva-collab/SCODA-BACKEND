// ===============================
// DASHBOARD.JS — SCODA
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    // ======================
    // MENSAJE DE ÉXITO
    // ======================
    const params = new URLSearchParams(window.location.search);
    if (params.get("status") === "success") {
        const msg = document.getElementById("status-message");
        if (msg) msg.classList.remove("d-none");
    }

    // ======================
    // CONFIGURACIÓN GLOBAL
    // ======================
    const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};

    if (ACCESS_TOKEN) localStorage.setItem("access_token", ACCESS_TOKEN);
    if (SCODA_API_KEY) localStorage.setItem("SCODA_API_KEY", SCODA_API_KEY);
    if (API_BASE_URL) localStorage.setItem("API_BASE_URL", API_BASE_URL);

    const token = localStorage.getItem("access_token");
    const apiKey = localStorage.getItem("SCODA_API_KEY");

    function getHeaders() {
        return {
            "Content-Type": "application/json",
            "Authorization": token ? `Bearer ${token}` : "",
            "X-API-Key": apiKey || "",
        };
    }

    // ======================
    // CARGAR CONTEOS
    // ======================
    async function cargarConteos() {
        try {
            const base = localStorage.getItem("API_BASE_URL");

            const endpoints = {
                usuarios: `${base}/api/usuarios`,
                alumnos: `${base}/api/alumnos`,
                cursos: `${base}/api/cursos`,
                personas: `${base}/api/personas`,
            };

            const [resUsuarios, resAlumnos, resCursos, resPersonas] = await Promise.all([
                fetch(endpoints.usuarios, { headers: getHeaders() }),
                fetch(endpoints.alumnos, { headers: getHeaders() }),
                fetch(endpoints.cursos, { headers: getHeaders() }),
                fetch(endpoints.personas, { headers: getHeaders() }),
            ]);

            const [usuarios, alumnos, cursos, personas] = await Promise.all([
                resUsuarios.json(),
                resAlumnos.json(),
                resCursos.json(),
                resPersonas.json(),
            ]);

            document.getElementById("usuarios-count").textContent = usuarios.length ?? "--";
            document.getElementById("alumnos-count").textContent = alumnos.length ?? "--";
            document.getElementById("cursos-count").textContent = cursos.length ?? "--";
            document.getElementById("personas-count").textContent = personas.length ?? "--";

        } catch (error) {
            console.error("Error al obtener conteos:", error);
        }
    }

    cargarConteos();

    // ======================
    // MODO OSCURO / CLARO
    // ======================
    const themeBtn = document.getElementById("toggle-theme");
    const currentTheme = localStorage.getItem("theme") || "light";

    document.body.dataset.theme = currentTheme;
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
        } else {
            icon.classList.replace("bi-brightness-high", "bi-moon-fill");
        }
    }
});
