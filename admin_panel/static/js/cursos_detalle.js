// =======================================================
//   SCODA — GESTIÓN DETALLE DE CURSO (VERSIÓN FINAL)
// =======================================================

document.addEventListener("DOMContentLoaded", () => {

    const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN, CURSO_ID } = window.SCODA_CONFIG || {};
    const token = ACCESS_TOKEN;

    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        "X-API-Key": SCODA_API_KEY
    };

    // ------------------------- ELEMENTOS -------------------------
    const cursoNombre = document.getElementById("curso-nombre");
    const cursoNivel = document.getElementById("curso-nivel");
    const cursoEstablecimiento = document.getElementById("curso-establecimiento");
    const cursoProfesorJefe = document.getElementById("curso-profesor-jefe");

    const tbodyAlumnos = document.getElementById("alumnos-curso-body");
    const inputBuscarAlumno = document.getElementById("buscar-alumno-input");
    const tbodyBuscador = document.getElementById("buscar-alumno-body");
    const loader = document.getElementById("loader");

    function showLoader() { loader.style.display = "flex"; }
    function hideLoader() { loader.style.display = "none"; }

    function notificar(msg, tipo = "success") {
        const div = document.getElementById("notificacion");
        div.className = `alert alert-${tipo} position-fixed top-0 end-0 m-3 shadow`;
        div.textContent = msg;
        setTimeout(() => { div.className = ""; div.textContent = ""; }, 2500);
    }

    // =======================================================
    //      1) CARGAR CURSO
    // =======================================================
    async function cargarCurso() {
        try {
            showLoader();

            const resp = await fetch(`${API_BASE_URL}/api/cursos/${CURSO_ID}`, { headers });
            if (!resp.ok) throw new Error("No se pudo obtener datos del curso");

            const curso = await resp.json();

            cursoNombre.textContent = curso.nombre;
            cursoNivel.textContent = curso.nivel;
            cursoEstablecimiento.textContent = curso.establecimiento?.nombre || "—";

            await cargarProfesores(curso.profesor?.id);

        } catch (error) {
            console.error(error);
            notificar("Error al cargar información del curso", "danger");
        } finally {
            hideLoader();
        }
    }

    // =======================================================
    //      2) CARGAR PROFESORES
    // =======================================================
    async function cargarProfesores(idActualProfesor) {
        try {
            const resp = await fetch(`${API_BASE_URL}/api/usuarios?rol=profesor`, { headers });
            const data = await resp.json();

            cursoProfesorJefe.innerHTML = "";

            (data.results || []).forEach(prof => {
                const opt = document.createElement("option");
                opt.value = prof.id;
                opt.textContent = `${prof.persona.nombres} ${prof.persona.apellido_uno}`;
                if (prof.id === idActualProfesor) opt.selected = true;
                cursoProfesorJefe.appendChild(opt);
            });

        } catch (err) {
            console.error(err);
        }
    }

    cursoProfesorJefe.addEventListener("change", async () => {
        try {
            showLoader();
            const body = { profesor: cursoProfesorJefe.value };

            const resp = await fetch(`${API_BASE_URL}/api/cursos/${CURSO_ID}`, {
                method: "PATCH",
                headers,
                body: JSON.stringify(body)
            });

            if (!resp.ok) throw new Error("Error al actualizar profesor jefe");

            notificar("Profesor Jefe actualizado correctamente");

        } catch (err) {
            console.error(err);
            notificar("Error al actualizar profesor jefe", "danger");
        } finally {
            hideLoader();
        }
    });

    // =======================================================
    //      3) CARGAR ALUMNOS DEL CURSO
    // =======================================================
    async function cargarAlumnosCurso() {
        try {
            showLoader();

            const resp = await fetch(`${API_BASE_URL}/api/cursos/${CURSO_ID}/alumnos`, { headers });
            if (!resp.ok) throw new Error("Error API alumnos curso");

            const data = await resp.json();

            tbodyAlumnos.innerHTML = "";

            (data.results || []).forEach((al, index) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${al.nombre_completo}</td>
                    <td>${al.rut}</td>
                    <td>${al.apoderado || "—"}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="quitarAlumno(${al.id})">
                            <i class="bi bi-x-circle"></i>
                        </button>
                    </td>
                `;
                tbodyAlumnos.appendChild(tr);
            });

        } catch (error) {
            console.error(error);
            notificar("Error al cargar alumnos del curso", "danger");
        } finally {
            hideLoader();
        }
    }

    window.cargarAlumnosCurso = cargarAlumnosCurso;

    // =======================================================
    //      4) QUITAR ALUMNO DEL CURSO
    // =======================================================
    window.quitarAlumno = async function (alumnoId) {
        if (!confirm("¿Seguro que deseas quitar a este alumno del curso?")) return;

        try {
            showLoader();

            const resp = await fetch(`${API_BASE_URL}/api/alumnos/${alumnoId}`, {
                method: "PATCH",
                headers,
                body: JSON.stringify({ curso: null })
            });

            if (!resp.ok) throw new Error("Error al quitar alumno");

            notificar("Alumno removido del curso");
            cargarAlumnosCurso();

        } catch (err) {
            console.error(err);
            notificar("No se pudo quitar el alumno", "danger");
        } finally {
            hideLoader();
        }
    };

    // =======================================================
    //      5) BUSCAR ALUMNOS
    // =======================================================
    inputBuscarAlumno.addEventListener("input", () => {
        const val = inputBuscarAlumno.value.trim();
        if (val.length >= 2) buscarAlumno(val);
        else tbodyBuscador.innerHTML = "";
    });

    async function buscarAlumno(texto) {
        try {
            // 🔥 RUTA CORRECTA SIN SLASH FINAL
            const resp = await fetch(`${API_BASE_URL}/api/alumnos?search=${texto}`, { headers });
            if (!resp.ok) return;

            const data = await resp.json();
            tbodyBuscador.innerHTML = "";

            (data.results || []).forEach((al, idx) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td>${al.persona.nombres} ${al.persona.apellido_uno}</td>
                    <td>${al.persona.run}</td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="agregarAlumno(${al.id})">
                            <i class="bi bi-check-circle"></i>
                        </button>
                    </td>
                `;
                tbodyBuscador.appendChild(tr);
            });

        } catch (err) {
            console.error(err);
        }
    }

    // =======================================================
    //      6) AGREGAR ALUMNO
    // =======================================================
    window.agregarAlumno = async function (alumnoId) {
        try {
            showLoader();

            const resp = await fetch(`${API_BASE_URL}/api/alumnos/${alumnoId}`, {
                method: "PATCH",
                headers,
                body: JSON.stringify({ curso: CURSO_ID })
            });

            if (!resp.ok) throw new Error("Error al agregar alumno");

            notificar("Alumno agregado al curso correctamente");
            cargarAlumnosCurso();

        } catch (err) {
            console.error(err);
            notificar("Error agregando alumno", "danger");
        } finally {
            hideLoader();
        }
    };

    // =======================================================
    //      INICIO
    // =======================================================
    cargarCurso();
    cargarAlumnosCurso();

});
