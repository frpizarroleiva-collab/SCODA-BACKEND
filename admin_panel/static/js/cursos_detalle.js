// =======================================================
//   SCODA — GESTIÓN DETALLE DE CURSO (VERSIÓN FINAL OK)
// =======================================================

document.addEventListener("DOMContentLoaded", () => {

    const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN, CURSO_ID } = window.SCODA_CONFIG || {};
    const token = ACCESS_TOKEN;

    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        "X-API-Key": SCODA_API_KEY
    };

    // ELEMENTOS
    const cursoNombre = document.getElementById("curso-nombre");
    const cursoNivel = document.getElementById("curso-nivel");
    const cursoEstablecimiento = document.getElementById("curso-establecimiento");
    const cursoProfesorJefe = document.getElementById("curso-profesor-jefe");

    const tbodyAlumnos = document.getElementById("alumnos-curso-body");
    const tbodyBuscador = document.getElementById("buscar-alumno-body");

    const modalAgregar = document.getElementById("modalAgregarAlumno");
    const loader = document.getElementById("loader");

    const modalAgregarBS = new bootstrap.Modal(modalAgregar);

    function showLoader() { loader.style.display = "flex"; }
    function hideLoader() { loader.style.display = "none"; }

    function notificar(msg, tipo = "success") {
        const div = document.getElementById("notificacion");
        div.className = `alert alert-${tipo} position-fixed top-0 end-0 m-3 shadow`;
        div.textContent = msg;
        setTimeout(() => { div.className = ""; div.textContent = ""; }, 2600);
    }

    // =======================================================
    // CARGAR CURSO
    // =======================================================
    async function cargarCurso() {
        try {
            showLoader();
            const resp = await fetch(`${API_BASE_URL}/api/cursos/${CURSO_ID}`, { headers });
            const curso = await resp.json();

            cursoNombre.textContent = curso.nombre;
            cursoNivel.textContent = curso.nivel;
            cursoEstablecimiento.textContent = curso.establecimiento_nombre || "—";

            await cargarProfesores(curso.profesor);

        } catch {
            notificar("Error al cargar curso", "danger");
        } finally {
            hideLoader();
        }
    }

    // =======================================================
    // PROFESORES
    // =======================================================
    async function cargarProfesores(idActualProfesor) {
        const resp = await fetch(`${API_BASE_URL}/api/personas/profesores`, { headers });
        const lista = await resp.json();

        cursoProfesorJefe.innerHTML = `<option value="">Sin profesor asignado</option>`;
        lista.forEach(prof => {
            const opt = document.createElement("option");
            opt.value = prof.id;
            opt.textContent = `${prof.nombres} ${prof.apellido_uno}`;
            if (prof.id === idActualProfesor) opt.selected = true;
            cursoProfesorJefe.appendChild(opt);
        });
    }

    cursoProfesorJefe.addEventListener("change", async () => {
        try {
            showLoader();

            const prof = cursoProfesorJefe.value || null;

            await fetch(`${API_BASE_URL}/api/cursos/${CURSO_ID}`, {
                method: "PATCH",
                headers,
                body: JSON.stringify({ profesor: prof })
            });

            notificar("Profesor Jefe actualizado");

        } catch {
            notificar("Error al actualizar profesor", "danger");
        } finally {
            hideLoader();
        }
    });

    // =======================================================
    // CHIP DE ESTADO
    // =======================================================
    function generarChipEstado(estado) {
        if (!estado) return `<span class="estado-chip estado-SIN">SIN REGISTRO</span>`;
        const clase = estado.replaceAll(" ", "_").toUpperCase();
        return `<span class="estado-chip estado-${clase}">${estado}</span>`;
    }

    // =======================================================
    // CARGAR ALUMNOS DEL CURSO
    // =======================================================
    async function cargarAlumnosCurso() {
        try {
            showLoader();

            const resp = await fetch(`${API_BASE_URL}/api/cursos/${CURSO_ID}/alumnos`, { headers });
            const data = await resp.json();

            tbodyAlumnos.innerHTML = "";

            (data.results || data || []).forEach((al, index) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${al.nombre_completo}</td>
                    <td>${al.rut}</td>
                    <td>${generarChipEstado(al.estado_actual)}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="quitarAlumno(${al.id})">
                            <i class="bi bi-x-circle"></i>
                        </button>
                    </td>
                `;
                tbodyAlumnos.appendChild(tr);
            });

        } catch {
            notificar("Error al cargar alumnos", "danger");
        } finally {
            hideLoader();
        }
    }
    window.cargarAlumnosCurso = cargarAlumnosCurso;

    // =======================================================
    // QUITAR ALUMNO
    // =======================================================
    window.quitarAlumno = async function (alumnoId) {
        if (!confirm("¿Seguro?")) return;

        try {
            showLoader();

            await fetch(`${API_BASE_URL}/api/alumnos/${alumnoId}`, {
                method: "PATCH",
                headers,
                body: JSON.stringify({ curso: null })
            });

            notificar("Alumno quitado");
            cargarAlumnosCurso();

        } catch {
            notificar("Error al quitar alumno", "danger");
        } finally {
            hideLoader();
        }
    };

    // =======================================================
    // BUSCAR
    // =======================================================
   async function buscarAlumno(texto) {
    const resp = await fetch(`${API_BASE_URL}/api/alumnos?search=${texto}`, { headers });
    const data = await resp.json();

    tbodyBuscador.innerHTML = "";

    // FIX DEFINITIVO: aceptar results O array directo
    (data.results || data || []).forEach((al, idx) => {

        const p = al.persona_detalle;  // TU API usa persona_detalle
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${p.nombres} ${p.apellido_uno}</td>
            <td>${p.run}</td>
            <td>
                <button class="btn btn-success btn-sm" onclick="agregarAlumno(${al.id})">
                    <i class="bi bi-check-circle"></i>
                </button>
            </td>
        `;
        tbodyBuscador.appendChild(tr);
    });
}

// =======================================================
// FIX DEFINITIVO: BUSCADOR SIN LISTENERS DUPLICADOS
// =======================================================
let listenerBuscar = null;

modalAgregar.addEventListener("shown.bs.modal", () => {

    const inputBuscarAlumno = document.getElementById("buscar-alumno-input");

    // reset tabla
    tbodyBuscador.innerHTML = "";
    inputBuscarAlumno.value = "";
    buscarAlumno("");

    // eliminar listener anterior si existe
    if (listenerBuscar) {
        inputBuscarAlumno.removeEventListener("input", listenerBuscar);
    }

    // definir listener nuevo
    listenerBuscar = () => {
    const val = inputBuscarAlumno.value.trim();

        // Buscar desde 1 letra
        if (val.length >= 1) {
            buscarAlumno(val);
        } else {
            // si está vacío, cargar todos
            buscarAlumno("");
        }
    };

    // aplicarlo
    inputBuscarAlumno.addEventListener("input", listenerBuscar);
});

    // =======================================================
    //AGREGAR ALUMNO
    // =======================================================
    window.agregarAlumno = async function (alumnoId) {
        try {
            showLoader();

            await fetch(`${API_BASE_URL}/api/alumnos/${alumnoId}`, {
                method: "PATCH",
                headers,
                body: JSON.stringify({ curso: parseInt(CURSO_ID) })
            });

            notificar("Alumno agregado");
            modalAgregarBS.hide();
            cargarAlumnosCurso();

        } catch {
            notificar("Error al agregar alumno", "danger");
        } finally {
            hideLoader();
        }
    };

    // =======================================================
    // INICIO
    // =======================================================
    cargarCurso();
    cargarAlumnosCurso();

});
