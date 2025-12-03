// =======================================
// CONFIG GLOBAL
// =======================================
const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};
const token = ACCESS_TOKEN;

// =======================================
// MODALES
// =======================================
const modalFamilia = new bootstrap.Modal(document.getElementById("modalForm"));
const modalEditar = new bootstrap.Modal(document.getElementById("modalEditar"));
const modalDetalle = new bootstrap.Modal(document.getElementById("modalDetalleAlumno"));

// =======================================
// ELEMENTOS PRINCIPALES
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

const buscadorInput = document.getElementById("buscadorAlumnos");

// Export
const btnExportCSV = document.getElementById("btnExportCSV");
const btnExportPDF = document.getElementById("btnExportPDF");

// Selects direcciones
const selectPais = formFamilia.querySelector("select[name='pais_apoderado']");
const selectRegion = formFamilia.querySelector("select[name='region_apoderado']");
const selectComuna = formFamilia.querySelector("select[name='comuna_apoderado']");

// =======================================
// VALIDAR RUN (FRONTEND)
// =======================================
function validarRunChile(run) {
    if (!run) return false;

    run = run.replace(/\./g, "").replace(/-/g, "").replace(/\s+/g, "").toUpperCase();
    if (run.length < 2) return false;

    const cuerpo = run.slice(0, -1);
    let dv = run.slice(-1);

    if (!/^\d+$/.test(cuerpo)) return false;

    let suma = 0;
    let multiplo = 2;

    for (let i = cuerpo.length - 1; i >= 0; i--) {
        suma += multiplo * parseInt(cuerpo[i]);
        multiplo = multiplo === 7 ? 2 : multiplo + 1;
    }

    const resto = 11 - (suma % 11);
    let dv_calculado = resto === 11 ? "0" : resto === 10 ? "K" : String(resto);

    return dv === dv_calculado;
}

// =======================================
// MANEJO DE ERRORES DEL BACKEND (NUEVO)
// =======================================
function mostrarErroresBackend(json) {
    if (!json) {
        mostrarNotificacion("Error desconocido del servidor", "#dc3545");
        return;
    }

    if (typeof json === "string") {
        mostrarNotificacion(json, "#dc3545");
        return;
    }

    if (json.error) {
        mostrarNotificacion(json.error, "#dc3545");
        return;
    }

    if (typeof json === "object") {
        const errores = [];

        for (const key in json) {
            if (Array.isArray(json[key])) {
                errores.push(`${key}: ${json[key].join(", ")}`);
            } else {
                errores.push(`${key}: ${json[key]}`);
            }
        }

        mostrarNotificacion(errores.join(" | "), "#dc3545");
    }
}

// =======================================
// VARIABLES
// =======================================
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

function mostrarNotificacion(msg, color = "#007BFF") {
    notificacion.textContent = msg;
    notificacion.style.background = color;
    notificacion.style.display = "block";
    setTimeout(() => (notificacion.style.display = "none"), 2600);
}

function mostrarLoader(show = true) {
    loader.style.display = show ? "flex" : "none";
}

function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        "X-API-KEY": SCODA_API_KEY
    };
}

// =======================================
// BOTÓN ABRIR MODAL
// =======================================
if (btnAbrir) {
    btnAbrir.addEventListener("click", () => modalFamilia.show());
}

// =======================================
// CARGA DE PAISES / REGIONES / COMUNAS
// =======================================
async function cargarPaises() {
    const res = await fetch(`${API_BASE_URL}/api/paises`, { headers: getHeaders() });
    paisesCache = await res.json();

    selectPais.innerHTML =
        `<option value="">Seleccione...</option>` +
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
    const paisID = parseInt(selectPais.value);

    const regiones = regionesCache.filter(r => r.pais === paisID);
    selectRegion.innerHTML =
        `<option value="">Seleccione...</option>` +
        regiones.map(r => `<option value="${r.id}">${escapeHTML(r.nombre)}</option>`).join("");

    selectComuna.innerHTML = `<option value="">Seleccione región primero</option>`;
});

selectRegion.addEventListener("change", () => {
    const regionID = parseInt(selectRegion.value);

    const comunas = comunasCache.filter(c => c.region === regionID);
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
// BLOQUES DINÁMICOS
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
<option value="Apoderado">Apoderado</option>
`;

// ---------------------------------------
// APODERADO EXTRA
// ---------------------------------------
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
                <label>Nombres</label>
                <input class="form-control nombre_extra">
            </div>

            <div class="col-md-4">
                <label>Apellido paterno</label>
                <input class="form-control apellido_uno_extra">
            </div>

            <div class="col-md-4">
                <label>Apellido materno</label>
                <input class="form-control apellido_dos_extra">
            </div>

            <div class="col-md-4">
                <label>RUN</label>
                <input class="form-control run_extra">
            </div>

            <div class="col-md-4">
                <label>Parentesco</label>
                <select class="form-select parentesco_extra">${opcionesParentesco}</select>
            </div>

            <div class="col-md-4">
                <label>Sexo</label>
                <select class="form-select sexo_extra">
                    <option value="">Seleccione...</option>
                    <option value="M">Masculino</option>
                    <option value="F">Femenino</option>
                    <option value="O">Otro</option>
                </select>
            </div>

            <div class="col-md-3 d-flex align-items-end">
                <label><input type="checkbox" class="autorizado_extra" checked> Autorizado</label>
            </div>

            <div class="col-md-1 d-flex align-items-end">
                <button type="button" class="btn btn-danger btn-sm btn-remove-apoderado">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;

    contenedorApoderadosExtra.appendChild(div);

    div.querySelector(".btn-remove-apoderado").addEventListener("click", () => div.remove());
}

// ---------------------------------------
// HIJO
// ---------------------------------------
function crearBloqueHijo() {
    const div = document.createElement("div");
    div.classList.add("bloque-hijo");

    div.innerHTML = `
        <h6 class="fw-bold text-success">Hijo</h6>
        <div class="row g-2">

            <div class="col-md-4">
                <label>Nombres</label>
                <input class="form-control nombre_hijo">
            </div>

            <div class="col-md-4">
                <label>Apellido paterno</label>
                <input class="form-control apellido_uno_hijo">
            </div>

            <div class="col-md-4">
                <label>Apellido materno</label>
                <input class="form-control apellido_dos_hijo">
            </div>

            <div class="col-md-4">
                <label>RUN</label>
                <input class="form-control run_hijo">
            </div>

            <div class="col-md-4">
                <label>Fecha nacimiento</label>
                <input type="date" class="form-control fecha_nac_hijo">
            </div>

            <div class="col-md-4">
                <label>Sexo</label>
                <select class="form-select sexo_hijo">
                    <option value="">Seleccione...</option>
                    <option value="M">Masculino</option>
                    <option value="F">Femenino</option>
                    <option value="O">Otro</option>
                </select>
            </div>

            <div class="col-md-4">
                <label>Curso</label>
                <select class="form-select curso_hijo">
                    <option value="">Seleccione...</option>
                    ${cursosCache.map(c => `<option value="${c.id}">${escapeHTML(c.nombre)}</option>`).join("")}
                </select>
            </div>

            <div class="col-md-12 d-flex justify-content-end mt-2">
                <button type="button" class="btn btn-danger btn-sm btn-remove-hijo">
                    <i class="bi bi-trash"></i> Quitar hijo
                </button>
            </div>
        </div>
    `;

    contenedorHijos.appendChild(div);

    div.querySelector(".btn-remove-hijo").addEventListener("click", () => div.remove());
}

btnAgregarHijo.addEventListener("click", crearBloqueHijo);
btnAgregarApoderadoExtra.addEventListener("click", crearBloqueApoderadoExtra);

// =======================================
// CREAR FAMILIA COMPLETA
// =======================================
formFamilia.addEventListener("submit", async e => {
    e.preventDefault();

    // VALIDACIÓN RUN APODERADO PRINCIPAL
    const runApoderado = formFamilia.run_apoderado.value;
    if (runApoderado && !validarRunChile(runApoderado)) {
        mostrarNotificacion("El RUN del apoderado principal no es válido", "#dc3545");
        return;
    }

    // VALIDACIÓN RUN APODERADOS EXTRAS
    let runInvalidoExtra = false;
    contenedorApoderadosExtra.querySelectorAll(".run_extra").forEach(input => {
        if (input.value && !validarRunChile(input.value)) runInvalidoExtra = true;
    });
    if (runInvalidoExtra) {
        mostrarNotificacion("Uno o más RUN de los apoderados adicionales no es válido", "#dc3545");
        return;
    }

    // VALIDACIÓN RUN HIJOS
    let runInvalidoHijo = false;
    contenedorHijos.querySelectorAll(".run_hijo").forEach(input => {
        if (input.value && !validarRunChile(input.value)) runInvalidoHijo = true;
    });
    if (runInvalidoHijo) {
        mostrarNotificacion("Uno o más RUN de los alumnos es inválido", "#dc3545");
        return;
    }

    // VALIDACIÓN DE NOMBRES OBLIGATORIOS (NUEVO)
    if (!formFamilia.nombres_apoderado.value.trim() ||
        !formFamilia.apellido_uno_apoderado.value.trim()) {
        mostrarNotificacion("El apoderado principal debe tener nombre y apellido.", "#dc3545");
        return;
    }

    let datosInvalidosExtra = false;
    contenedorApoderadosExtra.querySelectorAll(".bloque-apoderado-extra").forEach(div => {
        const nom = div.querySelector(".nombre_extra").value.trim();
        const ape = div.querySelector(".apellido_uno_extra").value.trim();
        if (!nom || !ape) datosInvalidosExtra = true;
    });
    if (datosInvalidosExtra) {
        mostrarNotificacion("Todos los apoderados adicionales deben tener nombre y apellido.", "#dc3545");
        return;
    }

    let datosInvalidosHijos = false;
    contenedorHijos.querySelectorAll(".bloque-hijo").forEach(div => {
        const nom = div.querySelector(".nombre_hijo").value.trim();
        const ape = div.querySelector(".apellido_uno_hijo").value.trim();
        if (!nom || !ape) datosInvalidosHijos = true;
    });
    if (datosInvalidosHijos) {
        mostrarNotificacion("Todos los alumnos deben tener nombre y apellido.", "#dc3545");
        return;
    }

    // VALIDACIÓN DE PARENTESCO (NUEVO)
    const parentescosValidos = ["Padre","Madre","Abuelo","Abuela","Tío","Tía","Hermano","Hermana","Otro","Apoderado"];
    let parentescoInvalido = false;
    contenedorApoderadosExtra.querySelectorAll(".parentesco_extra").forEach(sel => {
        if (sel.value && !parentescosValidos.includes(sel.value)) parentescoInvalido = true;
    });
    if (parentescoInvalido) {
        mostrarNotificacion("Uno o más parentescos no son válidos.", "#dc3545");
        return;
    }

    // --------------------------------------------
    // INICIO ENVÍO
    // --------------------------------------------
    mostrarLoader(true);
    const btnSubmit = formFamilia.querySelector("button[type='submit']");
    if (btnSubmit) btnSubmit.disabled = true;

    const direccionPrincipal = {
        calle: formFamilia.calle_apoderado.value,
        numero: formFamilia.numero_apoderado.value,
        depto: formFamilia.depto_apoderado.value,
        comuna_id: formFamilia.comuna_apoderado.value
    };

    const apoderadoPrincipal = {
        nombres: formFamilia.nombres_apoderado.value,
        apellido_uno: formFamilia.apellido_uno_apoderado.value,
        apellido_dos: formFamilia.apellido_dos_apoderado.value,
        run: formFamilia.run_apoderado.value,
        email: formFamilia.email_apoderado.value,
        fono: formFamilia.fono_apoderado.value,
        sexo: formFamilia.sexo_apoderado.value,

        pais_nacionalidad_id: formFamilia.pais_apoderado.value,
        region_id: formFamilia.region_apoderado.value,
        comuna_id: formFamilia.comuna_apoderado.value,

        direccion: direccionPrincipal,

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
            sexo: div.querySelector(".sexo_extra").value,

            direccion: direccionPrincipal,
            comuna_id: apoderadoPrincipal.comuna_id,
            pais_nacionalidad_id: apoderadoPrincipal.pais_nacionalidad_id
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
            sexo: div.querySelector(".sexo_hijo").value,
            curso_id: div.querySelector(".curso_hijo").value,

            direccion: direccionPrincipal,
            comuna_id: apoderadoPrincipal.comuna_id,
            pais_nacionalidad_id: apoderadoPrincipal.pais_nacionalidad_id
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
    if (btnSubmit) btnSubmit.disabled = false;

    const json = await res.json();

    if (!res.ok) {
        mostrarErroresBackend(json);
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
// LISTAR ALUMNOS
// =======================================
async function cargarAlumnos() {
    mostrarLoader(true);
    tablaBody.innerHTML = "";

    const res = await fetch(`${API_BASE_URL}/api/alumnos`, { headers: getHeaders() });
    const data = await res.json();

    mostrarLoader(false);

    data.sort((a, b) => a.id - b.id);

    tablaBody.innerHTML = data.map((a, index) => {
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
            </tr>
        `;
    }).join("");
}

// =======================================
// BUSCADOR
// =======================================
let buscadorTimer = null;

if (buscadorInput) {
    buscadorInput.addEventListener("input", () => {
        clearTimeout(buscadorTimer);

        buscadorTimer = setTimeout(() => {
            const texto = buscadorInput.value.toLowerCase().trim();
            const filas = document.querySelectorAll("#tablaAlumnos tbody tr");

            filas.forEach(fila => {
                fila.style.display = fila.textContent.toLowerCase().includes(texto) ? "" : "none";
            });

        }, 200);
    });
}

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

    formEditar.fecha_nacimiento.value = persona.fecha_nacimiento || "";
    formEditar.sexo.value = persona.sexo || "";

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

    const payload = {
        nombres: formEditar.nombres.value,
        apellido_uno: formEditar.apellido_uno.value,
        apellido_dos: formEditar.apellido_dos.value,
        run: formEditar.run.value,
        curso_id: formEditar.curso_id.value,
        fecha_nacimiento: formEditar.fecha_nacimiento.value || null,
        sexo: formEditar.sexo.value
    };

    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });

    mostrarLoader(false);

    if (!res.ok) {
        const err = await res.json();
        mostrarErroresBackend(err);
        return;
    }

    mostrarNotificacion("Alumno actualizado correctamente", "#28a745");
    modalEditar.hide();
    cargarAlumnos();
});

// =======================================
// ELIMINAR ALUMNO
// =======================================
let alumnoAEliminar = null;

function eliminarAlumno(id) {
    alumnoAEliminar = id;
    const modal = new bootstrap.Modal(document.getElementById("modalConfirmarEliminar"));
    modal.show();
}

document.getElementById("btnConfirmarEliminar").addEventListener("click", async () => {
    if (!alumnoAEliminar) return;

    mostrarLoader(true);

    const res = await fetch(`${API_BASE_URL}/api/alumnos/${alumnoAEliminar}`, {
        method: "DELETE",
        headers: getHeaders()
    });

    mostrarLoader(false);

    alumnoAEliminar = null;

    if (!res.ok) {
        const err = await res.json();
        mostrarErroresBackend(err);
        return;
    }

    mostrarNotificacion("Alumno eliminado correctamente", "#28a745");
    cargarAlumnos();

    const modal = bootstrap.Modal.getInstance(document.getElementById("modalConfirmarEliminar"));
    modal.hide();
});

// =======================================
// DETALLE ALUMNO
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
        contenedor.innerHTML = `<p class="text-danger text-center">Error al cargar datos.</p>`;
        return;
    }

    alumnoSeleccionado = data;

    const a = data.alumno;
    const apoderados = data.apoderados;
    const autorizados = data.autorizados;

    contenedor.innerHTML = `
        <div class="text-center mb-3">
            <div class="rounded-circle bg-success text-white d-inline-flex justify-content-center align-items-center"
                 style="width:80px;height:80px;font-size:32px;font-weight:bold;">
                ${escapeHTML(a.nombre.charAt(0))}${escapeHTML(a.apellido.charAt(0))}
            </div>

            <h4 class="text-success fw-bold mt-3">${a.nombre} ${a.apellido}</h4>
            <p><strong>RUN:</strong> ${a.run}</p>
            <p><strong>Curso:</strong> ${a.curso || "—"}</p>
            <p><strong>Establecimiento:</strong> ${a.establecimiento || "—"}</p>
        </div>

        <hr>

        <h6 class="fw-bold text-primary">Apoderados</h6>
        ${
            apoderados.length
                ? `<ul class="list-group mb-3">
                    ${apoderados.map(x => `
                        <li class="list-group-item">
                            <strong>${escapeHTML(x.nombre)}</strong>
                            <span class="badge bg-info ms-2">${escapeHTML(x.parentesco)}</span><br>
                            <small>RUN: ${escapeHTML(x.run)} | Tel: ${escapeHTML(x.telefono || "—")} | ${escapeHTML(x.correo || "—")}</small>
                        </li>
                    `).join("")}
                </ul>`
                : `<p class="text-muted">Sin apoderados registrados</p>`
        }

        <h6 class="fw-bold text-primary">Personas Autorizadas</h6>
        ${
            autorizados.length
                ? `<ul class="list-group mb-3">
                    ${autorizados.map(x => `
                        <li class="list-group-item">
                            <strong>${escapeHTML(x.nombre)}</strong>
                            <span class="badge ${x.autorizado ? "bg-success" : "bg-danger"} ms-2">
                                ${x.autorizado ? "Autorizado" : "No autorizado"}
                            </span><br>
                            <small>${escapeHTML(x.parentesco || "—")} | Tel: ${escapeHTML(x.telefono || "—")} | ${escapeHTML(x.correo || "—")}</small>
                        </li>
                    `).join("")}
                </ul>`
                : `<p class="text-muted">Sin autorizados registrados</p>`
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

    apoderados.forEach(x => {
        csv += `${x.nombre};${x.run};${x.telefono};${x.correo};${x.parentesco}\n`;
    });

    csv += `\nAutorizados:\nNombre;Parentesco;Teléfono;Correo;Estado\n`;

    autorizados.forEach(x => {
        csv += `${x.nombre};${x.parentesco};${x.telefono};${x.correo};${x.autorizado ? "Autorizado" : "No Autorizado"}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `ficha_alumno_${alumno.run}.csv`;
    link.click();
};

// =======================================
// EXPORTAR PDF
// =======================================
btnExportPDF.onclick = () => {
    if (!alumnoSeleccionado) return;
    window.print();
};

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
