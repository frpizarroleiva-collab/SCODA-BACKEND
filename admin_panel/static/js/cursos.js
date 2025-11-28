// ==================
// GESTIÓN DE CURSOS
// ==================

const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG;
const API_URL = `${API_BASE_URL}/api/cursos`;

if (ACCESS_TOKEN && !localStorage.getItem("access_token")) {
    localStorage.setItem("access_token", ACCESS_TOKEN);
}
const token = localStorage.getItem("access_token");

// ---------------------------------------------------------------
//  HEADERS BASE
// ---------------------------------------------------------------
function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": token ? `Bearer ${token}` : "",
        "X-API-Key": SCODA_API_KEY,
    };
}

// ---------------------------------------------------------------
//  UTILIDADES
// ---------------------------------------------------------------
function mostrarLoader(mostrar = true, texto = "Cargando...") {
    const loader = document.getElementById("loader");
    loader.style.display = mostrar ? "flex" : "none";
    const span = loader.querySelector("span");
    if (span) span.textContent = texto;
}

function notificar(mensaje, tipo = "success") {
    const div = document.getElementById("notificacion");
    div.className = `alert alert-${tipo} position-fixed top-0 end-0 m-3 shadow`;
    div.textContent = mensaje;
    div.style.display = "block";
    setTimeout(() => (div.style.display = "none"), 3000);
}

// ---------------------------------------------------------------
//  CARGAR SELECTS
// ---------------------------------------------------------------
async function cargarSelects() {
    try {
        const [profRes, estRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/personas/profesores`, { headers: getHeaders() }),
            fetch(`${API_BASE_URL}/api/establecimientos`, { headers: getHeaders() }),
        ]);

        const profesores = await profRes.json();
        const establecimientos = await estRes.json();

        const profesorSelect = document.getElementById("profesor");
        const estSelect = document.getElementById("establecimiento");

        profesorSelect.innerHTML = `<option value="">Sin profesor asignado</option>`;
        profesores.forEach((p) => {
            profesorSelect.innerHTML += `<option value="${p.id}">${p.nombres} ${p.apellido_uno}</option>`;
        });

        estSelect.innerHTML = `<option value="">Seleccione establecimiento</option>`;
        establecimientos.forEach((e) => {
            estSelect.innerHTML += `<option value="${e.id}">${e.nombre}</option>`;
        });

    } catch (error) {
        console.error(error);
        notificar("Error al cargar listas de selección.", "danger");
    }
}

// ---------------------------------------------------------------
//  CARGAR CURSOS
// ---------------------------------------------------------------
async function cargarCursos() {
    mostrarLoader(true);
    try {
        const res = await fetch(API_URL, { headers: getHeaders() });
        if (!res.ok) throw new Error(`Error ${res.status}`);
        const cursos = await res.json();

        const tbody = document.querySelector("#cursos-table tbody");
        tbody.innerHTML = "";

        cursos.forEach((c, i) => {
            const inicio = c.hora_inicio ? c.hora_inicio.slice(0, 5) : "08:00";
            const termino = c.hora_termino ? c.hora_termino.slice(0, 5) : "15:30";

            tbody.innerHTML += `
                <tr data-id="${c.id}">
                    <td>${i + 1}</td>
                    <td>${c.nombre}</td>
                    <td>${c.nivel}</td>
                    <td>${c.profesor_nombre || "—"}</td>
                    <td>${c.establecimiento_nombre || "—"}</td>

                    <td><input type="time" id="inicio-${c.id}" class="form-control form-control-sm" value="${inicio}"></td>
                    <td><input type="time" id="termino-${c.id}" class="form-control form-control-sm" value="${termino}"></td>

                    <td>
                        <button class="btn btn-primary btn-sm me-1" onclick="actualizarHorario(${c.id})">
                            <i class="bi bi-save"></i>
                        </button>
                        <button class="btn btn-info btn-sm me-1" onclick="irDetalleCurso(${c.id})">
                            <i class="bi bi-people"></i>
                        </button>
                        <button class="btn btn-warning btn-sm me-1" onclick="editarCurso(${c.id})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="abrirConfirmacionEliminar(${c.id}, '${c.nombre}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>`;
        });

    } catch (error) {
        console.error(error);
        notificar("Error al cargar cursos.", "danger");
    } finally {
        mostrarLoader(false);
    }
}

// ---------------------------------------------------------------
//  DETALLE DE CURSO
// ---------------------------------------------------------------
function irDetalleCurso(id) {
    window.location.href = `/panel/cursos/${id}/`;
}

// ---------------------------------------------------------------
//  ACTUALIZAR HORARIO
// ---------------------------------------------------------------
async function actualizarHorario(id) {
    const hora_inicio = document.getElementById(`inicio-${id}`).value;
    const hora_termino = document.getElementById(`termino-${id}`).value;

    try {
        const res = await fetch(`${API_URL}/${id}/actualizar-horario`, {
            method: "PUT",
            headers: getHeaders(),
            body: JSON.stringify({ hora_inicio, hora_termino }),
        });

        const data = await res.json();
        if (res.ok) notificar("Horario actualizado correctamente.");
        else notificar(data.error || "Error al actualizar horario.", "danger");

    } catch (error) {
        console.error(error);
        notificar("Error al guardar horario.", "danger");
    }
}

// ---------------------------------------------------------------
//  ABRIR MODAL CURSO
// ---------------------------------------------------------------
function abrirModal(curso = null) {
    const modal = new bootstrap.Modal(document.getElementById("modalCurso"));
    document.getElementById("cursoForm").reset();
    document.getElementById("cursoIdHidden").value = curso?.id || "";
    document.getElementById("modalTitulo").textContent = curso ? "Editar Curso" : "Nuevo Curso";

    if (curso) {
        document.getElementById("nombre").value = curso.nombre;
        document.getElementById("nivel").value = curso.nivel;
        document.getElementById("profesor").value = curso.profesor || "";
        document.getElementById("establecimiento").value =
            curso.establecimiento_obj ? curso.establecimiento_obj.id : "";
    }

    modal.show();
}

// ---------
//  EDITAR
// ---------
async function editarCurso(id) {
    try {
        const res = await fetch(`${API_URL}/${id}`, { headers: getHeaders() });
        const curso = await res.json();
        abrirModal(curso);
    } catch {
        notificar("Error al cargar el curso.", "danger");
    }
}

// -----------------------------------------
//  GUARDAR (POST o PATCH)
// -----------------------------------------
async function guardarCurso(e) {
    e.preventDefault();

    const id = document.getElementById("cursoIdHidden").value;
    const method = id ? "PATCH" : "POST";
    const url = id ? `${API_URL}/${id}` : API_URL;

    const profesorRaw = document.getElementById("profesor").value;
    const establecimientoRaw = document.getElementById("establecimiento").value;

    const payload = {
        nombre: document.getElementById("nombre").value,
        nivel: parseInt(document.getElementById("nivel").value),
    };

    if (profesorRaw !== "") payload.profesor = parseInt(profesorRaw);
    if (establecimientoRaw !== "") payload.establecimiento = parseInt(establecimientoRaw);

    try {
        const res = await fetch(url, {
            method,
            headers: getHeaders(),
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
            notificar(data.detail || "Error al guardar curso.", "danger");
            return;
        }

        notificar("Curso guardado correctamente.");
        bootstrap.Modal.getInstance(document.getElementById("modalCurso")).hide();
        cargarCursos();

    } catch (error) {
        console.error(error);
        notificar("Error general al guardar curso.", "danger");
    }
}

// -----------------------------
// MODAL CONFIRMACIÓN ELIMINAR
// -----------------------------

let cursoAEliminar = null;

// ➕ AGREGADO: abrir modal bonito
function abrirConfirmacionEliminar(id, nombre) {
    cursoAEliminar = id;
    document.getElementById("confirm-delete-text").textContent =
        `¿Seguro que deseas eliminar el curso "${nombre}"?`;

    const modal = new bootstrap.Modal(document.getElementById("modalConfirmDelete"));
    modal.show();
}

document.getElementById("btnConfirmDelete").addEventListener("click", async () => {
    if (!cursoAEliminar) return;

    mostrarLoader(true, "Eliminando curso...");

    try {
        const res = await fetch(`${API_URL}/${cursoAEliminar}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        mostrarLoader(false);

        const modal = bootstrap.Modal.getInstance(document.getElementById("modalConfirmDelete"));
        modal.hide(); 

        if (res.status === 204) {
            notificar("Curso eliminado correctamente.");
            document.querySelector(`tr[data-id="${cursoAEliminar}"]`)?.remove();
        } else {
            notificar("Error al eliminar el curso.", "danger");
        }

    } catch (error) {
        mostrarLoader(false);
        notificar("Error inesperado al eliminar.", "danger");
    }
});


// -------------
//  INICIALIZAR
// -------------
document.addEventListener("DOMContentLoaded", () => {
    cargarSelects().then(cargarCursos);
});
