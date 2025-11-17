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

// Select buscador
const buscadorInput = document.getElementById("buscadorAlumnos");

// Selects para apoderado principal
const selectPais = formFamilia.querySelector("select[name='pais_apoderado']");
const selectRegion = formFamilia.querySelector("select[name='region_apoderado']");
const selectComuna = formFamilia.querySelector("select[name='comuna_apoderado']");

let paisesCache = [];
let regionesCache = [];
let comunasCache = [];
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
    return v == null ? "" : v;
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
// CARGA: PAÍSES – REGIONES – COMUNAS
// =======================================
async function cargarPaises() {
    const res = await fetch(`${API_BASE_URL}/api/paises`, { headers: getHeaders() });
    paisesCache = await res.json();

    selectPais.innerHTML = `<option value="">Seleccione...</option>` +
        paisesCache.map(p => `<option value="${p.id}">${escapeHTML(p.nombre)}</option>`).join("");
}

async function cargarRegiones() {
    const res = await fetch(`${API_BASE_URL}/api/regiones`, { headers: getHeaders() });
    regionesCache = await res.json();
}

async function cargarComunas() {
    const res = await fetch(`${API_BASE_URL}/api/comunas`, { headers: getHeaders() });
    comunasCache = await res.json();
}

selectPais.addEventListener("change", () => {
    const paisID = selectPais.value;

    const regiones = regionesCache.filter(r => r.pais === parseInt(paisID));
    selectRegion.innerHTML =
        `<option value="">Seleccione...</option>` +
        regiones.map(r => `<option value="${r.id}">${escapeHTML(r.nombre)}</option>`).join("");

    selectComuna.innerHTML = `<option value="">Seleccione región primero</option>`;
});

selectRegion.addEventListener("change", () => {
    const regionID = selectRegion.value;

    const comunas = comunasCache.filter(c => c.region === parseInt(regionID));
    selectComuna.innerHTML =
        `<option value="">Seleccione...</option>` +
        comunas.map(c => `<option value="${c.id}">${escapeHTML(c.nombre)}</option>`).join("");
});

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
// LISTAR ALUMNOS
// =======================================
async function cargarAlumnos() {
    mostrarLoader(true);
    tablaBody.innerHTML = "";

    const res = await fetch(`${API_BASE_URL}/api/alumnos`, { headers: getHeaders() });
    let data = await res.json();

    data.sort((a, b) => a.id - b.id);

    tablaBody.innerHTML = data
        .map((a, index) => {
            const persona = a.persona_detalle || {};
            const curso = a.curso_detalle?.nombre || "-";

            return `
                <tr>
                    <td>${index + 1}</td>
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
        })
        .join("");

    mostrarLoader(false);
}

// =======================================
// 🔍 BUSCADOR RÁPIDO (DEBOUNCE)
// =======================================
let buscadorTimer = null;

if (buscadorInput) {
    buscadorInput.addEventListener("input", () => {
        clearTimeout(buscadorTimer);

        buscadorTimer = setTimeout(() => {
            const texto = buscadorInput.value.toLowerCase().trim();
            const filas = document.querySelectorAll("#tablaAlumnos tbody tr");

            filas.forEach(fila => {
                const contenido = fila.textContent.toLowerCase();
                fila.style.display = contenido.includes(texto) ? "" : "none";
            });

        }, 250);
    });
}

// =======================================
// BLOQUES: APODERADOS EXTRA
// =======================================
const opcionesParentesco = `
    <option value="Padre">Padre</option>
    <option value="Madre">Madre</option>
    <option value="Abuelo">Abuelo</option>
    <option value="Abuela">Abuela</option>
    <option value="Tío">Tío</option>
    <option value="Tía">Tía</option>
    <option value="Hermano">Hermano</option>
    <option value="Hermana">Hermana</option>
    <option value="Otro">Otro</option>
`;

function crearBloqueApoderadoExtra() {
    if (contenedorApoderadosExtra.children.length >= 2) {
        mostrarNotificacion("Máximo 2 apoderados adicionales.", "#dc3545");
        return;
    }

    const div = document.createElement("div");
    div.classList.add("bloque-apoderado-extra");

    div.innerHTML = `
        <h6 class="fw-bold text-success">Apoderado adicional</h6>
        <div class="row g-2">

            <div class="col-md-4">
                <label class="fw-semibold">Nombres</label>
                <input class="form-control nombre_extra">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Apellido paterno</label>
                <input class="form-control apellido_uno_extra">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Apellido materno</label>
                <input class="form-control apellido_dos_extra">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">RUN</label>
                <input class="form-control run_extra">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Parentesco</label>
                <select class="form-select parentesco_extra">
                    ${opcionesParentesco}
                </select>
            </div>

            <div class="col-md-3 d-flex align-items-end">
                <label><input type="checkbox" class="autorizado_extra" checked> Autorizado</label>
            </div>

            <div class="col-md-1 d-flex align-items-end">
                <button type="button" class="btn btn-danger btn-sm delete" onclick="this.closest('.bloque-apoderado-extra').remove()">
                    <i class="bi bi-trash"></i>
                </button>
            </div>

        </div>
    `;

    contenedorApoderadosExtra.appendChild(div);
}

// =======================================
// BLOQUES: HIJOS
// =======================================
function crearBloqueHijo() {
    const div = document.createElement("div");
    div.classList.add("bloque-hijo");

    div.innerHTML = `
        <h6 class="fw-bold text-success">Hijo</h6>
        <div class="row g-2">

            <div class="col-md-4">
                <label class="fw-semibold">Nombres</label>
                <input class="form-control nombre_hijo">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Apellido paterno</label>
                <input class="form-control apellido_uno_hijo">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Apellido materno</label>
                <input class="form-control apellido_dos_hijo">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">RUN</label>
                <input class="form-control run_hijo">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Fecha nacimiento</label>
                <input type="date" class="form-control fecha_nac_hijo">
            </div>

            <div class="col-md-4">
                <label class="fw-semibold">Curso</label>
                <select class="form-select curso_hijo">
                    <option value="">Seleccione...</option>
                    ${cursosCache.map(c => `<option value="${c.id}">${escapeHTML(c.nombre)}</option>`).join("")}
                </select>
            </div>

            <div class="col-md-12 d-flex justify-content-end mt-2">
                <button type="button" class="btn btn-danger btn-sm delete" onclick="this.closest('.bloque-hijo').remove()">
                    <i class="bi bi-trash"></i> Quitar hijo
                </button>
            </div>

        </div>
    `;

    contenedorHijos.appendChild(div);
}

// =======================================
// CREAR FAMILIA COMPLETA
// =======================================
formFamilia.addEventListener("submit", async e => {
    e.preventDefault();
    mostrarLoader(true);

    const apoderadoPrincipal = {
        nombres: formFamilia.nombres_apoderado.value,
        apellido_uno: formFamilia.apellido_uno_apoderado.value,
        apellido_dos: formFamilia.apellido_dos_apoderado.value,
        run: formFamilia.run_apoderado.value,
        email: formFamilia.email_apoderado.value,
        fono: formFamilia.fono_apoderado.value,
        pais_nacionalidad_id: formFamilia.pais_apoderado.value,
        region_id: formFamilia.region_apoderado.value,
        comuna_id: formFamilia.comuna_apoderado.value,
        direccion: formFamilia.direccion_apoderado.value,
        fecha_nacimiento: formFamilia.fecha_nac_apoderado.value || null,
        parentesco: formFamilia.parentesco_apoderado.value,
        autorizado: formFamilia.autorizado.checked
    };

    const apoderadosExtra = [];
    contenedorApoderadosExtra.querySelectorAll(".bloque-apoderado-extra").forEach(div => {
        apoderadosExtra.push({
            nombres: div.querySelector(".nombre_extra").value,
            apellido_uno: div.querySelector(".apellido_uno_extra").value,
            apellido_dos: div.querySelector(".apellido_dos_extra").value,
            run: div.querySelector(".run_extra").value,
            parentesco: div.querySelector(".parentesco_extra").value,
            autorizado: div.querySelector(".autorizado_extra").checked,

            direccion: apoderadoPrincipal.direccion,
            region_id: apoderadoPrincipal.region_id,
            comuna_id: apoderadoPrincipal.comuna_id,
            pais_nacionalidad_id: apoderadoPrincipal.pais_nacionalidad_id,
            fecha_nacimiento: null
        });
    });

    const alumnos = [];
    contenedorHijos.querySelectorAll(".bloque-hijo").forEach(div => {
        alumnos.push({
            nombres: div.querySelector(".nombre_hijo").value,
            apellido_uno: div.querySelector(".apellido_uno_hijo").value,
            apellido_dos: div.querySelector(".apellido_dos_hijo").value,
            run: div.querySelector(".run_hijo").value,
            fecha_nacimiento: div.querySelector(".fecha_nac_hijo").value || null,
            direccion: apoderadoPrincipal.direccion,
            comuna_id: apoderadoPrincipal.comuna_id,
            region_id: apoderadoPrincipal.region_id,
            pais_nacionalidad_id: apoderadoPrincipal.pais_nacionalidad_id,
            curso_id: div.querySelector(".curso_hijo").value
        });
    });

    const payload = {
        apoderado_principal: apoderadoPrincipal,
        apoderados_extras: apoderadosExtra,
        alumnos
    };

    const res = await fetch(`${API_BASE_URL}/api/alumnos/crear-familia`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });

    mostrarLoader(false);

    const json = await res.json();

    if (!res.ok) {
        mostrarNotificacion(json.error || "Error al crear familia", "#dc3545");
        return;
    }

    mostrarNotificacion("Familia registrada correctamente", "#28a745");

    formFamilia.reset();
    contenedorApoderadosExtra.innerHTML = "";
    contenedorHijos.innerHTML = "";
    crearBloqueHijo();
    modalFamilia.hide();
    cargarAlumnos();
});

// =======================================
// EDITAR ALUMNO (PATCH REAL)
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
    formEditar.fecha_nacimiento.value = persona.fecha_nacimiento || "";

    formEditar.curso_id.innerHTML =
        cursosCache.map(c =>
            `<option value="${c.id}" ${a.curso_detalle && c.id == a.curso_detalle.id ? "selected" : ""}>${escapeHTML(c.nombre)}</option>`
        ).join("");

    modalEditar.show();
}

formEditar.addEventListener("submit", async e => {
    e.preventDefault();
    mostrarLoader(true);

    const id = formEditar.id.value;

    const payload = {};

    if (formEditar.nombres.value.trim() !== "") payload.nombres = formEditar.nombres.value;
    if (formEditar.apellido_uno.value.trim() !== "") payload.apellido_uno = formEditar.apellido_uno.value;
    payload.apellido_dos = formEditar.apellido_dos.value;

    payload.run = formEditar.run.value;
    payload.curso_id = formEditar.curso_id.value;
    payload.fecha_nacimiento = formEditar.fecha_nacimiento.value || null;

    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });

    mostrarLoader(false);

    if (!res.ok) {
        mostrarNotificacion("Error al actualizar alumno", "#dc3545");
        return;
    }

    mostrarNotificacion("Alumno actualizado correctamente", "#28a745");
    modalEditar.hide();
    cargarAlumnos();
});

// =======================================
// ELIMINAR
// =======================================
async function eliminarAlumno(id) {
    if (!confirm("¿Eliminar alumno? Esta acción no se puede deshacer.")) return;

    mostrarLoader(true);

    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, {
        method: "DELETE",
        headers: getHeaders()
    });

    mostrarLoader(false);

    if (!res.ok) {
        mostrarNotificacion("Error al eliminar alumno", "#dc3545");
        return;
    }

    mostrarNotificacion("Alumno eliminado", "#28a745");
    cargarAlumnos();
}

// =======================================
// DETALLE ALUMNO (MODAL)
// =======================================
async function verDetalleAlumno(id) {
    const contenedor = document.getElementById("detalleAlumnoContainer");

    contenedor.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-success"></div>
            <p class="mt-2">Cargando información...</p>
        </div>
    `;

    modalDetalle.show();

    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}/detalle`, { headers: getHeaders() });
    const data = await res.json();

    if (!res.ok) {
        contenedor.innerHTML = `<p class="text-danger text-center">Error al cargar</p>`;
        return;
    }

    alumnoSeleccionado = data;

    const alumno = data.alumno;
    const apoderados = data.apoderados ?? [];
    const autorizados = data.autorizados ?? [];

    contenedor.innerHTML = `
        <div class="text-center mb-3">
            <div class="rounded-circle bg-success text-white d-inline-flex justify-content-center align-items-center"
                 style="width:80px;height:80px;font-size:32px;font-weight:bold;">
                ${escapeHTML(alumno.nombre.charAt(0) || "")}${escapeHTML(alumno.apellido.charAt(0) || "")}
            </div>

            <h4 class="text-success fw-bold mt-3">${alumno.nombre} ${alumno.apellido}</h4>

            <p><strong>RUN:</strong> ${alumno.run}</p>
            <p><strong>Curso:</strong> ${alumno.curso || "—"}</p>
            <p><strong>Establecimiento:</strong> ${alumno.establecimiento || "—"}</p>
        </div>

        <hr>

        <h6 class="fw-bold text-primary">Apoderados</h6>
        ${
            apoderados.length
                ? `<ul class="list-group mb-3">
                    ${apoderados.map(a => `
                        <li class="list-group-item">
                            <strong>${a.nombre}</strong>
                            <span class="badge bg-info ms-2">${a.parentesco}</span><br>
                            <small>RUN: ${a.run} | Tel: ${a.telefono || "—"} | ${a.correo || "—"}</small>
                        </li>
                    `).join("")}
                </ul>`
                : `<p class="text-muted">Sin apoderados registrados</p>`
        }

        <h6 class="fw-bold text-primary">Personas Autorizadas</h6>
        ${
            autorizados.length
                ? `<ul class="list-group">
                    ${autorizados.map(a => `
                        <li class="list-group-item">
                            <strong>${a.nombre}</strong>
                            <span class="badge ${a.autorizado ? "bg-success" : "bg-danger"} ms-2">
                                ${a.autorizado ? "Autorizado" : "No autorizado"}
                            </span><br>
                            <small>${a.parentesco || "—"} | Tel: ${a.telefono || "—"} | ${a.correo || "—"}</small>
                        </li>
                    `).join("")}
                </ul>`
                : `<p class="text-muted">Sin personas autorizadas</p>`
        }
    `;
}

// =======================================
// EXPORTAR CSV
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

// =======================================
// PDF (PRINT)
// =======================================
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
    await cargarPaises();
    await cargarRegiones();
    await cargarComunas();
    await cargarCursos();
    await cargarAlumnos();
    crearBloqueHijo();
});
