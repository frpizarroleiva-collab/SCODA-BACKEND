// =======================================
// CONFIGURACIÓN GLOBAL
// =======================================
const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};
const token = ACCESS_TOKEN;

// =======================================
// MODALES BOOTSTRAP
// =======================================
const modalFamilia = new bootstrap.Modal(document.getElementById("modalForm"));
const modalEditar = new bootstrap.Modal(document.getElementById("modalEditar"));
const modalDetalle = new bootstrap.Modal(document.getElementById("modalDetalleAlumno"));

// =======================================
// ELEMENTOS
// =======================================
const btnAbrir = document.getElementById("btnAbrirModal");
const formFamilia = document.getElementById("formFamilia");
const formEditar = document.getElementById("formEditar");
const contenedorHijos = document.getElementById("contenedorHijos");
const contenedorApoderadosExtra = document.getElementById("contenedorApoderadosExtra");
const btnAgregarHijo = document.getElementById("btnAgregarHijo");
const btnAgregarApoderadoExtra = document.getElementById("btnAgregarApoderadoExtra");
const tablaBody = document.querySelector("#tablaAlumnos tbody");
const notificacion = document.getElementById("notificacion");
const loader = document.getElementById("loader");
const btnExportCSV = document.getElementById("btnExportCSV");
const btnExportPDF = document.getElementById("btnExportPDF");

let cursosCache = [];
let alumnoSeleccionado = null;

// =======================================
// UTILIDADES
// =======================================
function escapeHTML(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function safe(v) {
    return v === undefined || v === null ? "" : v;
}

function mostrarNotificacion(mensaje, color = "#007BFF") {
    notificacion.textContent = mensaje;
    notificacion.style.background = color;
    notificacion.style.display = "block";
    setTimeout(() => (notificacion.style.display = "none"), 2500);
}

function mostrarLoader(mostrar) {
    loader.style.display = mostrar ? "flex" : "none";
}

function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        "X-API-KEY": SCODA_API_KEY
    };
}

// =======================================
// CARGAR CURSOS
// =======================================
async function cargarCursos() {
    mostrarLoader(true);
    const res = await fetch(`${API_BASE_URL}/api/cursos`, { headers: getHeaders() });
    cursosCache = await res.json();
    mostrarLoader(false);
}

// =======================================
// CARGAR ALUMNOS
// =======================================
async function cargarAlumnos() {
    mostrarLoader(true);
    tablaBody.innerHTML = "";

    const res = await fetch(`${API_BASE_URL}/api/alumnos`, { headers: getHeaders() });
    const data = await res.json();

    data.forEach(a => {
        const persona = a.persona_detalle || {};
        const curso = a.curso_detalle?.nombre || "-";

        tablaBody.innerHTML += `
            <tr>
                <td>${escapeHTML(a.id)}</td>
                <td>${escapeHTML(persona.run || "-")}</td>
                <td>${escapeHTML(`${safe(persona.nombres)} ${safe(persona.apellido_uno)}`)}</td>
                <td>${escapeHTML(curso)}</td>
                <td class="acciones">
                    <button class="btn btn-outline-success btn-sm me-1" onclick="verDetalleAlumno(${a.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-warning btn-sm me-1" onclick="abrirEditar(${a.id})">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="eliminarAlumno(${a.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>`;
    });

    mostrarLoader(false);
}

// =======================================
// APODERADO EXTRA
// =======================================
function crearBloqueApoderadoExtra() {
    if (contenedorApoderadosExtra.children.length >= 2) {
        mostrarNotificacion("Máximo 2 apoderados adicionales.", "#dc3545");
        return;
    }

    const div = document.createElement("div");
    div.classList.add("border", "rounded", "p-2", "mb-2");

    div.innerHTML = `
        <h6 class="fw-bold">Apoderado adicional</h6>

        <div class="row g-2">
            <div class="col-md-4">
                <input type="text" class="form-control nombre_extra" placeholder="Nombres" required>
            </div>

            <div class="col-md-4">
                <input type="text" class="form-control apellido_uno_extra" placeholder="Apellido Paterno" required>
            </div>

            <div class="col-md-4">
                <input type="text" class="form-control apellido_dos_extra" placeholder="Apellido Materno">
            </div>

            <div class="col-md-4">
                <input type="text" class="form-control run_extra" placeholder="RUN" required>
            </div>

            <div class="col-md-4">
                <select class="form-select parentesco_extra" required>
                    <option value="Padre">Padre</option>
                    <option value="Madre">Madre</option>
                    <option value="Abuelo">Abuelo</option>
                    <option value="Abuela">Abuela</option>
                    <option value="Tío">Tío</option>
                    <option value="Tía">Tía</option>
                    <option value="Otro">Otro</option>
                </select>
            </div>

            <div class="col-md-2 d-flex align-items-center">
                <input type="checkbox" class="form-check-input autorizado_extra" checked> Autorizado
            </div>

            <div class="col-md-2 d-flex align-items-center">
                <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('div.border').remove()">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;

    contenedorApoderadosExtra.appendChild(div);
}

// =======================================
// AÑADIR HIJO
// =======================================
function crearBloqueHijo() {
    const div = document.createElement("div");
    div.classList.add("border", "rounded", "p-2", "mb-2");

    div.innerHTML = `
        <h6 class="fw-bold">Hijo</h6>

        <div class="row g-2">
            <div class="col-md-4">
                <input type="text" class="form-control nombre_hijo" placeholder="Nombres" required>
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control apellido_uno_hijo" placeholder="Apellido Paterno" required>
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control apellido_dos_hijo" placeholder="Apellido Materno">
            </div>

            <div class="col-md-4">
                <input type="text" class="form-control run_hijo" placeholder="RUN" required>
            </div>

            <div class="col-md-6">
                <select class="form-select curso_hijo" required>
                    <option value="">Seleccione curso...</option>
                    ${cursosCache.map(c => `<option value="${c.id}">${escapeHTML(c.nombre)}</option>`).join("")}
                </select>
            </div>

            <div class="col-md-2 d-flex align-items-center">
                <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('div.border').remove()">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;

    contenedorHijos.appendChild(div);
}

// =======================================
// CREAR FAMILIA (CORREGIDO 100%)
// =======================================
formFamilia.addEventListener("submit", async e => {
    e.preventDefault();
    mostrarLoader(true);

    // --- Apoderado principal ---
    const apoderadoPrincipal = {
        nombres: formFamilia.nombres_apoderado.value,
        apellido_uno: formFamilia.apellido_uno_apoderado.value,
        apellido_dos: formFamilia.apellido_dos_apoderado.value,
        run: formFamilia.run_apoderado.value,
        email: formFamilia.email_apoderado.value,
        fono: formFamilia.fono_apoderado.value,
        parentesco: formFamilia.parentesco_apoderado.value,
        autorizado: formFamilia.autorizado.checked
    };

    // --- Apoderados extra ---
    const apoderadosExtra = [];
    contenedorApoderadosExtra.querySelectorAll(".border").forEach(div => {
        apoderadosExtra.push({
            nombres: div.querySelector(".nombre_extra").value,
            apellido_uno: div.querySelector(".apellido_uno_extra").value,
            apellido_dos: div.querySelector(".apellido_dos_extra").value,
            run: div.querySelector(".run_extra").value,
            parentesco: div.querySelector(".parentesco_extra").value,
            autorizado: div.querySelector(".autorizado_extra").checked,
            email: "",
            fono: ""
        });
    });

    // --- Hijos ---
    const alumnos = [];
    contenedorHijos.querySelectorAll(".border").forEach(div => {
        alumnos.push({
            nombres: div.querySelector(".nombre_hijo").value,
            apellido_uno: div.querySelector(".apellido_uno_hijo").value,
            apellido_dos: div.querySelector(".apellido_dos_hijo").value,
            run: div.querySelector(".run_hijo").value,
            curso_id: div.querySelector(".curso_hijo").value
        });
    });

    // --- Payload corregido ---
    const payload = {
        apoderado_principal: apoderadoPrincipal,
        apoderados_extras: apoderadosExtra,
        alumnos
    };

    // --- URL corregida ---
    const res = await fetch(`${API_BASE_URL}/api/alumnos/crear-familia`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });

    mostrarLoader(false);
    const json = await res.json();

    if (!res.ok) {
        mostrarNotificacion(json.error || "Error al crear familia.", "#dc3545");
        return;
    }

    mostrarNotificacion("Familia registrada con éxito.", "#28a745");

    formFamilia.reset();
    contenedorHijos.innerHTML = "";
    contenedorApoderadosExtra.innerHTML = "";

    crearBloqueHijo();

    modalFamilia.hide();
    cargarAlumnos();
});

// =======================================
// EDITAR ALUMNO
// =======================================
async function abrirEditar(id) {
    mostrarLoader(true);
    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, { headers: getHeaders() });
    const a = await res.json();
    mostrarLoader(false);

    const persona = a.persona_detalle;

    formEditar.id.value = a.id;
    formEditar.nombres.value = safe(persona.nombres);
    formEditar.apellido_uno.value = safe(persona.apellido_uno);
    formEditar.apellido_dos.value = safe(persona.apellido_dos);
    formEditar.run.value = persona.run;

    formEditar.curso_id.innerHTML = cursosCache.map(c =>
        `<option value="${c.id}" ${a.curso_detalle && c.id == a.curso_detalle.id ? "selected" : ""}>${escapeHTML(c.nombre)}</option>`
    ).join("");

    modalEditar.show();
}

formEditar.addEventListener("submit", async e => {
    e.preventDefault();
    mostrarLoader(true);

    const id = formEditar.id.value;
    const payload = { curso: formEditar.curso_id.value };

    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });

    mostrarLoader(false);

    if (res.ok) {
        mostrarNotificacion("Alumno actualizado correctamente.", "#28a745");
        modalEditar.hide();
        cargarAlumnos();
    } else {
        mostrarNotificacion("Error al actualizar alumno.", "#dc3545");
    }
});

// =======================================
// ELIMINAR ALUMNO
// =======================================
async function eliminarAlumno(id) {
    if (!confirm("¿Seguro que deseas eliminar este alumno?")) return;

    mostrarLoader(true);
    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, {
        method: "DELETE",
        headers: getHeaders()
    });
    mostrarLoader(false);

    if (res.ok) {
        mostrarNotificacion("Alumno eliminado correctamente.", "#28a745");
        cargarAlumnos();
    } else {
        mostrarNotificacion("Error al eliminar alumno.", "#dc3545");
    }
}

// =======================================
// VER DETALLE
// =======================================
async function verDetalleAlumno(id) {
    const contenedor = document.getElementById("detalleAlumnoContainer");

    contenedor.innerHTML = `
        <div class="text-center text-muted py-4">
            <div class="spinner-border text-success"></div>
            <p class="mt-2 mb-0">Cargando información del alumno...</p>
        </div>
    `;

    modalDetalle.show();

    try {
        const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}/detalle`, { headers: getHeaders() });
        const data = await res.json();

        if (!res.ok) throw new Error();

        alumnoSeleccionado = data;

        const alumno = data.alumno;
        const apoderados = data.apoderados || [];
        const autorizados = data.autorizados || [];

        const inicialNombre = escapeHTML(alumno.nombre.charAt(0) || "");
        const inicialApellido = escapeHTML(alumno.apellido.charAt(0) || "");

        contenedor.innerHTML = `
            <div class="text-center mb-3">
                <div class="rounded-circle bg-success text-white d-inline-flex justify-content-center align-items-center"
                     style="width: 80px; height: 80px; font-size: 32px; font-weight: bold;">
                    ${inicialNombre}${inicialApellido}
                </div>

                <h4 class="text-success fw-bold mt-3">
                    ${escapeHTML(alumno.nombre)} ${escapeHTML(alumno.apellido)}
                </h4>

                <p><strong>RUN:</strong> ${escapeHTML(alumno.run)}</p>
                <p><strong>Curso:</strong> ${escapeHTML(alumno.curso || "—")}</p>
                <p><strong>Establecimiento:</strong> ${escapeHTML(alumno.establecimiento || "—")}</p>
            </div>

            <hr>

            <h6 class="fw-bold text-primary">
                <i class="bi bi-people-fill"></i> Apoderados
            </h6>

            ${
                apoderados.length
                ? `
                    <ul class="list-group mb-3">
                        ${apoderados.map(a => `
                            <li class="list-group-item">
                                <strong>${escapeHTML(a.nombre)}</strong>
                                <span class="badge bg-info ms-2">${escapeHTML(a.parentesco)}</span>
                                <br>
                                <small>
                                    RUN: ${escapeHTML(a.run || "—")} |
                                    Tel: ${escapeHTML(a.telefono || "—")} |
                                    ${escapeHTML(a.correo || "—")}
                                </small>
                            </li>
                        `).join("")}
                    </ul>
                `
                : `<p class="text-muted">Sin apoderados registrados.</p>`
            }

            <h6 class="fw-bold text-primary">
                <i class="bi bi-person-badge"></i> Personas Autorizadas
            </h6>

            ${
                autorizados.length
                ? `
                    <ul class="list-group">
                        ${autorizados.map(a => `
                            <li class="list-group-item">
                                <strong>${escapeHTML(a.nombre)}</strong>
                                <span class="badge ${a.autorizado ? "bg-success" : "bg-danger"} ms-2">
                                    ${a.autorizado ? "Autorizado" : "No autorizado"}
                                </span>
                                <br>
                                <small>
                                    ${escapeHTML(a.parentesco || "—")} |
                                    Tel: ${escapeHTML(a.telefono || "—")} |
                                    ${escapeHTML(a.correo || "—")}
                                </small>
                            </li>
                        `).join("")}
                    </ul>
                `
                : `<p class="text-muted">Sin personas autorizadas.</p>`
            }
        `;
    } catch (err) {
        contenedor.innerHTML = `<p class="text-danger text-center">Error al cargar detalle del alumno.</p>`;
    }
}

// =======================================
// EXPORTAR CSV Y PDF
// =======================================
btnExportCSV.onclick = () => {
    if (!alumnoSeleccionado) return;

    const { alumno, apoderados, autorizados } = alumnoSeleccionado;

    let csv = `Alumno;RUN;Curso;Establecimiento
${alumno.nombre} ${alumno.apellido};${alumno.run};${alumno.curso};${alumno.establecimiento}

Apoderados:
Nombre;RUN;Teléfono;Correo;Parentesco
`;

    apoderados.forEach(a => {
        csv += `${a.nombre};${a.run};${a.telefono};${a.correo};${a.parentesco}\n`;
    });

    csv += `

Autorizados:
Nombre;Parentesco;Teléfono;Correo;Estado
`;

    autorizados.forEach(a => {
        csv += `${a.nombre};${a.parentesco};${a.telefono};${a.correo};${a.autorizado ? "Autorizado" : "No autorizado"}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `ficha_alumno_${alumno.run}.csv`;
    link.click();
};

btnExportPDF.onclick = () => {
    if (!alumnoSeleccionado) return;
    window.print();
};

// =======================================
// EVENTOS
// =======================================
btnAgregarHijo.onclick = () => crearBloqueHijo();
btnAgregarApoderadoExtra.onclick = () => crearBloqueApoderadoExtra();
btnAbrir.onclick = () => modalFamilia.show();

// =======================================
// INICIALIZACIÓN
// =======================================
document.addEventListener("DOMContentLoaded", async () => {
    await cargarCursos();
    await cargarAlumnos();
    crearBloqueHijo();
});
