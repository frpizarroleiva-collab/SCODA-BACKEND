// =====================================================================
//     SCODA — REPORTES DE RETIROS (VERSIÓN FINAL MEJORADA)
// =====================================================================

document.addEventListener("DOMContentLoaded", () => {

    // -------------------------------------------------------
    // CONFIG GLOBAL
    // -------------------------------------------------------
    const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG;

    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${ACCESS_TOKEN}`,
        "X-API-Key": SCODA_API_KEY,
    };

    // -------------------------------------------------------
    // ELEMENTOS
    // -------------------------------------------------------
    const selectCurso = document.getElementById("selectCurso");
    const inputFecha = document.getElementById("inputFecha");
    const btnBuscar = document.getElementById("btnBuscar");
    const btnExportar = document.getElementById("btnExportar");
    const tablaRetiros = document.getElementById("tablaRetiros");

    const modalFoto = new bootstrap.Modal(document.getElementById("modalFoto"));
    const imgFoto = document.getElementById("imgFotoRetiro");

    // Loader estilo CURSOS (pantalla completa)
    const loader = document.getElementById("loader");

    function showLoader() {
        loader.style.display = "flex";
    }

    function hideLoader() {
        loader.style.display = "none";
    }

    // =======================================================
    // FORMATO FECHA Y HORA (CORREGIDO)
    // =======================================================

    // ⚠ NO usamos new Date(fechaStr) porque causa desfase de 1 día (UTC)
    function formatFecha(fechaISO) {
        if (!fechaISO) return "-";
        const [year, month, day] = fechaISO.split("-");
        return `${day}-${month}-${year}`;
    }

    function formatHora(horaStr) {
        if (!horaStr) return "-";

        // Si viene en formato "21:55:01", tomamos solo HH:MM
        if (horaStr.includes(":")) {
            return horaStr.substring(0, 5);
        }

        // Manejo alternativo por seguridad
        const d = new Date(horaStr);
        const hh = d.getHours().toString().padStart(2, "0");
        const mm = d.getMinutes().toString().padStart(2, "0");
        return `${hh}:${mm}`;
    }

    // =======================================================
    // CARGAR CURSOS
    // =======================================================
    async function cargarCursos() {
        try {
            const res = await fetch(`${API_BASE_URL}/api/cursos`, { headers });

            if (!res.ok) throw new Error("Error HTTP cargando cursos");

            const cursos = await res.json();

            selectCurso.innerHTML = `<option value="">Seleccione un curso...</option>`;

            cursos.forEach(c => {
                selectCurso.innerHTML += `<option value="${c.id}">${c.nombre}</option>`;
            });

        } catch (error) {
            console.error("Error cargando cursos:", error);
            alert("Error al cargar los cursos.");
        }
    }

    cargarCursos();

    // =======================================================
    // BUSCAR RETIROS
    // =======================================================
    async function buscarRetiros() {

        const cursoId = selectCurso.value;
        const fecha = inputFecha.value;

        if (!cursoId || !fecha) {
            alert("Debe seleccionar un curso y una fecha.");
            return;
        }

        const url = `${API_BASE_URL}/api/estado-alumnos/retiros?curso_id=${cursoId}&fecha=${fecha}`;

        try {
            showLoader();

            const res = await fetch(url, { headers });

            if (!res.ok) throw new Error("Error HTTP buscando retiros");

            const data = await res.json();

            renderTabla(data.alumnos || []);

            btnExportar.classList.toggle(
                "d-none",
                !(data.alumnos && data.alumnos.length)
            );

        } catch (error) {
            console.error("Error buscando retiros:", error);
            alert("Ocurrió un error al cargar los retiros.");
        } finally {
            hideLoader();
        }
    }

    // =======================================================
    // RENDER TABLA (SIN RUN)
    // =======================================================
    function renderTabla(listado) {

        if (!listado || listado.length === 0) {
            tablaRetiros.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-muted py-4">
                        No hay retiros registrados para esta fecha y curso.
                    </td>
                </tr>
            `;
            return;
        }

        tablaRetiros.innerHTML = "";

        listado.forEach(item => {
            tablaRetiros.innerHTML += `
                <tr>
                    <td>${item.alumno_nombre}</td>
                    <td>${item.curso_nombre}</td>
                    <td>${formatFecha(item.fecha)}</td>
                    <td>${formatHora(item.hora_registro)}</td>
                    <td>${item.estado}</td>
                    <td>${item.quien_retiro || "-"}</td>
                    <td>${item.parentesco || "-"}</td>
                    <td>${item.quien_registro || "-"}</td>
                    <td>${item.observacion || ""}</td>
                    <td>
                        ${
                            item.foto_documento
                                ? `<button class="btn btn-sm btn-outline-success" onclick="verFoto('${item.foto_documento}')">
                                        <i class="bi bi-image"></i>
                                   </button>`
                                : "-"
                        }
                    </td>
                </tr>
            `;
        });
    }

    // =======================================================
    // VER FOTO (BASE64) EN MODAL
    // =======================================================
    window.verFoto = function (base64) {
        imgFoto.src = base64.startsWith("data:")
            ? base64
            : `data:image/jpeg;base64,${base64}`;
        modalFoto.show();
    };

    // =======================================================
    // EXPORTAR CSV (SIN RUN Y SIN FOTO)
    // =======================================================
    async function exportarCSV() {

        const cursoId = selectCurso.value;
        const fecha = inputFecha.value;

        if (!cursoId || !fecha) {
            alert("Debe seleccionar curso y fecha.");
            return;
        }

        const url = `${API_BASE_URL}/api/estado-alumnos/retiros?curso_id=${cursoId}&fecha=${fecha}`;

        try {
            showLoader();

            const res = await fetch(url, { headers });
            const data = await res.json();

            const alumnos = data.alumnos || [];

            if (alumnos.length === 0) {
                alert("No hay datos para exportar.");
                return;
            }

            let csv = "Alumno,Curso,Fecha,Hora,Estado,Retirado por,Parentesco,Registrado por,Comentario\n";

            alumnos.forEach(item => {
                csv += `"${item.alumno_nombre}",`;
                csv += `"${item.curso_nombre}",`;
                csv += `"${formatFecha(item.fecha)}",`;
                csv += `"${formatHora(item.hora_registro)}",`;
                csv += `"${item.estado}",`;
                csv += `"${item.quien_retiro || ""}",`;
                csv += `"${item.parentesco || ""}",`;
                csv += `"${item.quien_registro || ""}",`;
                csv += `"${item.observacion || ""}"\n`;
            });

            const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = `reporte_retiros_${fecha}.csv`;
            link.click();

        } catch (error) {
            console.error("Error exportando CSV:", error);
            alert("No se pudo exportar el CSV.");
        } finally {
            hideLoader();
        }
    }

    btnExportar.addEventListener("click", exportarCSV);

    // =======================================================
    // EVENTOS
    // =======================================================
    btnBuscar.addEventListener("click", buscarRetiros);

});
