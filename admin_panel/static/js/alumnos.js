// =======================================
// CONFIGURACIÓN GLOBAL
// =======================================
const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};
const token = ACCESS_TOKEN;

// =======================================
// ELEMENTOS
// =======================================
const modalFamilia = document.getElementById("modalForm");
const modalEditar = document.getElementById("modalEditar");
const btnAbrir = document.getElementById("btnAbrirModal");
const btnCerrar = document.getElementById("cerrarModal");
const btnCerrarEditar = document.getElementById("cerrarEditar");
const formFamilia = document.getElementById("formFamilia");
const formEditar = document.getElementById("formEditar");
const contenedorHijos = document.getElementById("contenedorHijos");
const btnAgregarHijo = document.getElementById("btnAgregarHijo");
const tablaBody = document.querySelector("#tablaAlumnos tbody");
const notificacion = document.getElementById("notificacion");
const loader = document.getElementById("loader");
const btnExportCSV = document.getElementById("btnExportCSV");
const btnExportPDF = document.getElementById("btnExportPDF");

let cursosCache = [];
let alumnoSeleccionado = null;

// =======================================
// FUNCIONES AUXILIARES
// =======================================
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
        "X-API-Key": SCODA_API_KEY
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
        const curso = a.curso_detalle ? a.curso_detalle.nombre : "-";
        tablaBody.innerHTML += `
            <tr>
                <td>${a.id}</td>
                <td>${persona.run || "-"}</td>
                <td>${persona.nombres || ""} ${persona.apellido_uno || ""}</td>
                <td>${curso}</td>
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
// CREAR BLOQUES DE HIJOS
// =======================================
function crearBloqueHijo(index) {
    const div = document.createElement("div");
    div.innerHTML = `
        <fieldset>
            <legend>Hijo ${index + 1}</legend>
            <input type="text" name="nombres_hijo_${index}" placeholder="Nombres" required>
            <input type="text" name="apellido_uno_hijo_${index}" placeholder="Apellido paterno" required>
            <input type="text" name="apellido_dos_hijo_${index}" placeholder="Apellido materno">
            <input type="text" name="run_hijo_${index}" placeholder="RUN" required>
            <label>Curso</label>
            <select name="curso_hijo_${index}" required>
                <option value="">Seleccione curso...</option>
                ${cursosCache.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('')}
            </select>
            <button type="button" class="delete" onclick="this.closest('fieldset').remove()">Eliminar</button>
        </fieldset>`;
    contenedorHijos.appendChild(div);
}

// =======================================
// CREAR FAMILIA (APODERADO + HIJOS)
// =======================================
formFamilia.addEventListener("submit", async (e) => {
    e.preventDefault();
    mostrarLoader(true);

    const apoderado = {
        nombres: formFamilia.nombres_apoderado.value,
        apellido_uno: formFamilia.apellido_uno_apoderado.value,
        apellido_dos: formFamilia.apellido_dos_apoderado.value,
        run: formFamilia.run_apoderado.value,
        email: formFamilia.email_apoderado.value,
        fono: formFamilia.fono_apoderado.value
    };

    const alumnos = [];
    [...contenedorHijos.children].forEach((child, i) => {
        alumnos.push({
            nombres: child.querySelector(`[name=nombres_hijo_${i}]`).value,
            apellido_uno: child.querySelector(`[name=apellido_uno_hijo_${i}]`).value,
            apellido_dos: child.querySelector(`[name=apellido_dos_hijo_${i}]`).value,
            run: child.querySelector(`[name=run_hijo_${i}]`).value,
            curso_id: child.querySelector(`[name=curso_hijo_${i}]`).value
        });
    });

    const payload = { apoderado, alumnos, autorizado: formFamilia.autorizado.checked };

    const res = await fetch(`${API_BASE_URL}/api/alumnos/crear-familia`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });

    const result = await res.json();
    mostrarLoader(false);

    if (res.ok) {
        mostrarNotificacion(result.mensaje || "Familia registrada con éxito.", "#28a745");
        modalFamilia.style.display = "none";
        formFamilia.reset();
        contenedorHijos.innerHTML = "";
        await cargarAlumnos();
        crearBloqueHijo(0);
    } else {
        mostrarNotificacion(result.error || "Error al crear familia.", "#dc3545");
    }
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
    formEditar.nombres.value = persona.nombres;
    formEditar.apellido_uno.value = persona.apellido_uno;
    formEditar.apellido_dos.value = persona.apellido_dos || "";
    formEditar.run.value = persona.run;
    formEditar.curso_id.innerHTML = cursosCache.map(c =>
        `<option value="${c.id}" ${a.curso_detalle && c.id == a.curso_detalle.id ? "selected" : ""}>${c.nombre}</option>`
    ).join('');
    modalEditar.style.display = "block";
}

formEditar.addEventListener("submit", async (e) => {
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
        modalEditar.style.display = "none";
        await cargarAlumnos();
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
        await cargarAlumnos();
    } else {
        mostrarNotificacion("Error al eliminar alumno.", "#dc3545");
    }
}

// =======================================
// VER DETALLE DE ALUMNO (ACTUALIZADO)
// =======================================
async function verDetalleAlumno(id) {
    const modalDetalle = new bootstrap.Modal(document.getElementById("modalDetalleAlumno"));
    const contenedor = document.getElementById("detalleAlumnoContainer");

    contenedor.innerHTML = `
        <div class="text-center text-muted py-4">
            <div class="spinner-border text-success" role="status"></div>
            <p class="mt-2 mb-0">Cargando información del alumno...</p>
        </div>`;
    modalDetalle.show();

    try {
        const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}/detalle`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Error al obtener detalle.");

        alumnoSeleccionado = data;
        const alumno = data.alumno;
        const apoderados = data.apoderados || [];
        const autorizados = data.autorizados || [];

        contenedor.innerHTML = `
            <div class="text-center mb-3">
                <div class="rounded-circle bg-success text-white d-inline-flex justify-content-center align-items-center"
                     style="width: 80px; height: 80px; font-size: 32px; font-weight: bold;">
                    ${alumno.nombre.charAt(0)}${alumno.apellido.charAt(0)}
                </div>
                <h5 class="text-success fw-bold mt-3">${alumno.nombre} ${alumno.apellido}</h5>
                <p><strong>RUN:</strong> ${alumno.run}</p>
                <p><strong>Curso:</strong> ${alumno.curso || "—"}</p>
                <p><strong>Establecimiento:</strong> ${alumno.establecimiento || "—"}</p>
            </div>
            <hr>

            <h6 class="fw-bold text-primary mb-2"><i class="bi bi-people-fill"></i> Apoderados</h6>
            ${
                apoderados.length
                    ? `<ul class="list-group mb-3">
                        ${apoderados.map(a => `
                            <li class="list-group-item">
                                <strong>${a.nombre}</strong> (${a.tipo_relacion})
                                <br><small>RUN: ${a.run || "—"} | Tel: ${a.telefono || "—"} | ${a.correo || "—"}</small>
                            </li>`).join("")}
                      </ul>`
                    : `<p class="text-muted">Sin apoderados registrados.</p>`
            }

            <h6 class="fw-bold text-primary mb-2"><i class="bi bi-person-badge"></i> Autorizados a Retiro</h6>
            ${
                autorizados.length
                    ? `<ul class="list-group">
                        ${autorizados.map(a => `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${a.nombre}</strong> 
                                    <span class="badge ${a.autorizado ? "bg-success" : "bg-danger"}">
                                        ${a.autorizado ? "Autorizado" : "No autorizado"}
                                    </span><br>
                                    <small>${a.tipo_relacion || "—"} | Tel: ${a.telefono || "—"} | ${a.correo || "—"}</small>
                                </div>
                            </li>`).join("")}
                      </ul>`
                    : `<p class="text-muted">Sin personas autorizadas.</p>`
            }
        `;
    } catch (error) {
        contenedor.innerHTML = `<p class="text-danger text-center">Error al cargar detalle del alumno.</p>`;
        console.error(error);
    }
}

// =======================================
// EXPORTAR CSV / PDF
// =======================================
btnExportCSV.addEventListener("click", () => {
    if (!alumnoSeleccionado) return;
    const { alumno, apoderados, autorizados } = alumnoSeleccionado;

    let csv = `Alumno;RUN;Curso;Establecimiento\n${alumno.nombre} ${alumno.apellido};${alumno.run};${alumno.curso};${alumno.establecimiento}\n\nApoderados:\nNombre;RUN;Teléfono;Correo;Relación\n`;
    (apoderados || []).forEach(a => {
        csv += `${a.nombre};${a.run};${a.telefono};${a.correo};${a.tipo_relacion}\n`;
    });

    csv += `\nAutorizados:\nNombre;Relación;Teléfono;Correo;Estado\n`;
    (autorizados || []).forEach(a => {
        csv += `${a.nombre};${a.tipo_relacion};${a.telefono};${a.correo};${a.autorizado ? "Autorizado" : "No autorizado"}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `ficha_alumno_${alumno.run}.csv`;
    link.click();
});

btnExportPDF.addEventListener("click", () => {
    if (!alumnoSeleccionado) return;
    window.print();
});

// =======================================
// EVENTOS DE MODAL Y DASHBOARD
// =======================================
btnAgregarHijo.onclick = () => crearBloqueHijo(contenedorHijos.children.length);
btnAbrir.onclick = () => (modalFamilia.style.display = "flex");
btnCerrar.onclick = () => (modalFamilia.style.display = "none");
btnCerrarEditar.onclick = () => (modalEditar.style.display = "none");
window.onclick = e => {
    if (e.target === modalFamilia) modalFamilia.style.display = "none";
    if (e.target === modalEditar) modalEditar.style.display = "none";
};

// =======================================
// INICIALIZACIÓN
// =======================================
document.addEventListener("DOMContentLoaded", async () => {
    await cargarCursos();
    await cargarAlumnos();
    crearBloqueHijo(0);
});
