// =======================================
// CONFIGURACIÓN GLOBAL
// =======================================
const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};
const token = ACCESS_TOKEN;

// =======================================
// ELEMENTOS
// =======================================
const modal = document.getElementById("modalForm");
const modalEditar = document.getElementById("modalEditar");
const btnAbrir = document.getElementById("btnAbrirModal");
const btnCerrar = document.getElementById("cerrarModal");
const btnCerrarEditar = document.getElementById("cerrarEditar");
const form = document.getElementById("formFamilia");
const formEditar = document.getElementById("formEditar");
const contenedorHijos = document.getElementById("contenedorHijos");
const btnAgregarHijo = document.getElementById("btnAgregarHijo");
const tablaBody = document.querySelector("#tablaAlumnos tbody");
const notificacion = document.getElementById("notificacion");
const loader = document.getElementById("loader");

let cursosCache = [];

// =======================================
// FUNCIONES AUXILIARES
// =======================================
function mostrarNotificacion(mensaje, color="#007BFF") {
    notificacion.textContent = mensaje;
    notificacion.style.background = color;
    notificacion.style.display = "block";
    setTimeout(() => notificacion.style.display = "none", 2500);
}

function mostrarLoader(mostrar) {
    loader.style.display = mostrar ? "flex" : "none";
}

// =======================================
// CARGAR CURSOS
// =======================================
async function cargarCursos() {
    mostrarLoader(true);
    const res = await fetch(`${API_BASE_URL}/api/cursos`, {
        headers: { 
            "Authorization": `Bearer ${token}`,
            "X-API-Key": SCODA_API_KEY 
        }
    });
    cursosCache = await res.json();
    mostrarLoader(false);
}

// =======================================
// CARGAR ALUMNOS
// =======================================
async function cargarAlumnos() {
    mostrarLoader(true);
    tablaBody.innerHTML = "";
    const res = await fetch(`${API_BASE_URL}/api/alumnos`, {
        headers: { 
            "Authorization": `Bearer ${token}`,
            "X-API-Key": SCODA_API_KEY 
        }
    });
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
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    mostrarLoader(true);

    const apoderado = {
        nombres: form.nombres_apoderado.value,
        apellido_uno: form.apellido_uno_apoderado.value,
        apellido_dos: form.apellido_dos_apoderado.value,
        run: form.run_apoderado.value,
        email: form.email_apoderado.value,
        fono: form.fono_apoderado.value
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

    const payload = { apoderado, alumnos, autorizado: form.autorizado.checked };

    const res = await fetch(`${API_BASE_URL}/api/alumnos/crear-familia`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            "X-API-Key": SCODA_API_KEY
        },
        body: JSON.stringify(payload)
    });

    const result = await res.json();
    mostrarLoader(false);

    if (res.ok) {
        mostrarNotificacion(result.mensaje || "Familia registrada con éxito.", "#28a745");
        modal.style.display = "none";
        form.reset();
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
    const res = await fetch(`${API_BASE_URL}/api/alumnos/${id}`, {
        headers: { "Authorization": `Bearer ${token}`, "X-API-Key": SCODA_API_KEY }
    });
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
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            "X-API-Key": SCODA_API_KEY
        },
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
        headers: { "Authorization": `Bearer ${token}`, "X-API-Key": SCODA_API_KEY }
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
// EVENTOS DE MODAL Y DASHBOARD
// =======================================
btnAgregarHijo.onclick = () => crearBloqueHijo(contenedorHijos.children.length);
btnAbrir.onclick = () => modal.style.display = "flex";
btnCerrar.onclick = () => modal.style.display = "none";
btnCerrarEditar.onclick = () => modalEditar.style.display = "none";
window.onclick = e => {
    if (e.target === modal) modal.style.display = "none";
    if (e.target === modalEditar) modalEditar.style.display = "none";
};

function volverDashboard() { window.location.href = "/panel/dashboard/"; }

// =======================================
// INICIALIZACIÓN
// =======================================
document.addEventListener("DOMContentLoaded", async () => {
    await cargarCursos();
    await cargarAlumnos();
    crearBloqueHijo(0);
});
