console.log("DASHBOARD JS CARGADO VERSION X");


// ======================================
// DASHBOARD.JS — SCODA (VERSIÓN FINAL CON LOADER)
// ======================================
document.addEventListener("DOMContentLoaded", () => {

    // ------------------------------
    // LOADER GLOBAL
    // ------------------------------
    function showLoader() {
        document.getElementById("scoda-loader").classList.remove("d-none");
    }

    function hideLoader() {
        document.getElementById("scoda-loader").classList.add("d-none");
    }

    // ------------------------------
    // MENSAJE DE ÉXITO LOGIN
    // ------------------------------
    const params = new URLSearchParams(window.location.search);
    if (params.get("status") === "success") {
        const msg = document.getElementById("status-message");
        if (msg) msg.classList.remove("d-none");
    }

    // ------------------------------
    // CONFIG GLOBAL TOKENS
    // ------------------------------
    const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};

    if (ACCESS_TOKEN) localStorage.setItem("access_token", ACCESS_TOKEN);
    if (SCODA_API_KEY) localStorage.setItem("SCODA_API_KEY", SCODA_API_KEY);
    if (API_BASE_URL) localStorage.setItem("API_BASE_URL", API_BASE_URL);

    const token = localStorage.getItem("access_token");
    const apiKey = localStorage.getItem("SCODA_API_KEY");
    const BASE = localStorage.getItem("API_BASE_URL");

    function getHeaders() {
        return {
            "Content-Type": "application/json",
            "Authorization": token ? `Bearer ${token}` : "",
            "X-API-Key": apiKey || "",
        };
    }

    // ============================================================
    // 1. CARGAR LISTA DE CURSOS PARA EL FILTRO
    // ============================================================
    async function cargarCursos() {
        try {
            const res = await fetch(`${BASE}/api/cursos`, { headers: getHeaders() });
            const data = await res.json();

            const select = document.getElementById("filtro-curso");
            select.innerHTML = `<option value="">Todos</option>`;

            data.forEach(curso => {
                const op = document.createElement("option");
                op.value = curso.id;
                op.textContent = curso.nombre;
                select.appendChild(op);
            });

        } catch (e) {
            console.error("Error cargando cursos:", e);
        }
    }

    cargarCursos();

    // ============================================================
    // 2. CARGAR TARJETAS (Resumen general)
    // ============================================================
    async function cargarTarjetas(cursoId = "") {
        try {
            const q = cursoId ? `?curso_id=${cursoId}` : "";

            const endpoints = {
                ausentes: `${BASE}/api/estado-alumnos/ausentes${q}`,
                extension: `${BASE}/api/estado-alumnos/extension${q}`,
                anticipados: `${BASE}/api/estado-alumnos/retiros-anticipados${q}`,
                retiros: `${BASE}/api/estado-alumnos/retiros${q}`,
            };

            const responses = await Promise.all([
                fetch(endpoints.ausentes, { headers: getHeaders() }),
                fetch(endpoints.extension, { headers: getHeaders() }),
                fetch(endpoints.anticipados, { headers: getHeaders() }),
                fetch(endpoints.retiros, { headers: getHeaders() }),
            ]);

            const [aus, ext, ant, ret] = await Promise.all(
                responses.map(r => r.json())
            );

            const totalAus = aus?.total_ausentes ?? 0;
            const totalExt = ext?.total_extension ?? 0;
            const totalAnt = ant?.total_retiros_anticipados ?? ant?.total_anticipados ?? 0;
            const totalRet = ret?.total_retiros ?? 0;

            document.getElementById("ausentes-count").textContent = totalAus;
            document.getElementById("extension-count").textContent = totalExt;
            document.getElementById("anticipados-count").textContent = totalAnt;
            document.getElementById("retiros-count").textContent = totalRet;

            actualizarGrafico({
                ausentes: totalAus,
                extension: totalExt,
                anticipados: totalAnt,
                retiros: totalRet
            });

        } catch (err) {
            console.error("Error cargando tarjetas:", err);
        }
    }

    // ============================================================
    // 3. LISTADOS RÁPIDOS (últimos 5)
    // ============================================================
    async function cargarListadosRapidos(cursoId = "") {
        const q = cursoId ? `?curso_id=${cursoId}` : "";

        const zonas = {
            retiros: "lista-retiros",
            ausentes: "lista-ausentes",
            extension: "lista-extension",
        };

        const urls = {
            retiros: `${BASE}/api/estado-alumnos/retiros${q}`,
            ausentes: `${BASE}/api/estado-alumnos/ausentes${q}`,
            extension: `${BASE}/api/estado-alumnos/extension${q}`,
        };

        for (let tipo in urls) {
            try {
                const res = await fetch(urls[tipo], { headers: getHeaders() });
                const data = await res.json();

                const lista = document.getElementById(zonas[tipo]);
                lista.innerHTML = "";

                (data.alumnos || []).slice(0, 5).forEach(item => {
                    const li = document.createElement("li");
                    li.className = "list-group-item";
                    li.innerHTML = `
                        <strong>${item.alumno_nombre}</strong><br>
                        <small>${item.curso_nombre || ""}</small><br>
                        <small class="text-muted">${item.hora_registro}</small>
                    `;
                    lista.appendChild(li);
                });

            } catch (e) {
                console.error("Error cargando listado:", e);
            }
        }
    }

    // ============================================================
    // 4. GRÁFICO (Chart.js)
    // ============================================================
    let chartEstados = null;

    function actualizarGrafico({ ausentes, extension, anticipados, retiros }) {
        const ctx = document.getElementById("grafico-estados");

        if (chartEstados) chartEstados.destroy();

        chartEstados = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Ausentes", "Extensión", "Anticipados", "Retiros"],
                datasets: [{
                    label: "Cantidad",
                    data: [ausentes, extension, anticipados, retiros],
                    backgroundColor: [
                        "#e63946",
                        "#8e44ad",
                        "#f4d03f",
                        "#2ecc71"
                    ],
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
            },
        });
    }

    // ============================================================
    // 5. CARGAR TODO (con loader)
    // ============================================================
    async function cargarTodo() {
        showLoader();
        const cursoSel = document.getElementById("filtro-curso").value;
        await cargarTarjetas(cursoSel);
        await cargarListadosRapidos(cursoSel);
        hideLoader();
    }

    cargarTodo();

    // ============================================================
    // 6. FILTRO POR CURSO
    // ============================================================
    document.getElementById("filtro-curso").addEventListener("change", () => {
        cargarTodo();
    });

    // ============================================================
    // 7. MODO OSCURO / CLARO
    // ============================================================
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
