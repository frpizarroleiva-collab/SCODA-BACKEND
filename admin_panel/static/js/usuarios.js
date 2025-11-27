// =======================================================
// CONFIG GLOBAL
// =======================================================
const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};
const API_URL = `${API_BASE_URL}/api/usuarios`;

const token = ACCESS_TOKEN || localStorage.getItem("access_token");
if (ACCESS_TOKEN) localStorage.setItem("access_token", ACCESS_TOKEN);

function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": token ? `Bearer ${token}` : "",
        "X-API-Key": SCODA_API_KEY,
    };
}

// =======================================================
// LOADER GLOBAL
// =======================================================
function showLoader(text = "Cargando...") {
    document.getElementById("loader-text").textContent = text;
    document.getElementById("loader").classList.add("show");
}

function hideLoader() {
    document.getElementById("loader").classList.remove("show");
}

// =======================================================
// TOAST NOTIFICACIÓN
// =======================================================
function showToast(msg, type = "success") {
    const toast = document.getElementById("notificacion");
    if (!toast) return;

    toast.style.background = type === "error" ? "#dc3545" : "#198754";
    toast.textContent = msg;
    toast.style.display = "block";

    setTimeout(() => (toast.style.display = "none"), 3200);
}

// =======================================================
// MODAL (crear/editar usuario)
// =======================================================
const modal = new bootstrap.Modal(document.getElementById("modalUsuario"));

function abrirModal(usuario = null) {
    document.getElementById("usuarioForm").reset();
    document.getElementById("usuarioEmailHidden").value = usuario?.email || "";
    document.getElementById("modalTitulo").textContent = usuario
        ? "Editar Usuario"
        : "Nuevo Usuario";

    if (usuario) {
        document.getElementById("first_name").value = usuario.first_name || "";
        document.getElementById("last_name").value = usuario.last_name || "";
        document.getElementById("email").value = usuario.email;
        document.getElementById("rol").value = usuario.rol;
        document.getElementById("activo").value = usuario.is_active ? "true" : "false";
    }

    modal.show();
}

// =======================================================
// CARGAR USUARIOS
// =======================================================
async function cargarUsuarios() {
    showLoader("Cargando usuarios...");

    try {
        const res = await fetch(API_URL, { headers: getHeaders() });
        if (!res.ok) throw new Error("No se pudo obtener usuarios");

        const raw = await res.json();
        const data = Array.isArray(raw) ? raw : raw.results || [];

        data.sort((a, b) => a.id - b.id);

        const tbody = document.querySelector("#usuarios-table tbody");
        tbody.innerHTML = data
            .map(
                (u, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${u.first_name} ${u.last_name}</td>
                    <td>${u.email}</td>
                    <td>${u.rol.toUpperCase()}</td>
                    <td>${u.is_active ? "Sí" : "No"}</td>
                    <td>
                        <button class="btn btn-warning btn-sm me-1" onclick="editarUsuario('${u.email}')">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="confirmarEliminarUsuario('${u.email}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `
            )
            .join("");

    } catch (err) {
        showToast(err.message, "error");
    } finally {
        hideLoader();
    }
}

// =======================================================
// GUARDAR (CREATE / UPDATE)
// =======================================================
async function guardarUsuario(e) {
    e.preventDefault();
    showLoader("Guardando usuario...");

    const emailHidden = document.getElementById("usuarioEmailHidden").value;
    const email = document.getElementById("email").value.trim();

    const url = emailHidden ? `${API_URL}/${emailHidden}` : API_URL;
    const method = emailHidden ? "PUT" : "POST";

    try {
        const passwordInput = document.getElementById("password").value;

        if (!emailHidden && (!passwordInput || passwordInput.length < 6)) {
            hideLoader();
            showToast("La contraseña debe tener mínimo 6 caracteres.", "error");
            return;
        }

        let usuario = {
            first_name: document.getElementById("first_name").value,
            last_name: document.getElementById("last_name").value,
            email,
            rol: document.getElementById("rol").value,
            is_active: document.getElementById("activo").value === "true",
        };

        if (!emailHidden) {
            usuario.password = passwordInput;
        } else if (passwordInput.trim() !== "") {
            usuario.password = passwordInput;
        }

        const res = await fetch(url, {
            method,
            headers: getHeaders(),
            body: JSON.stringify(usuario),
        });

        if (!res.ok) {
            const error = await res.json();

            let msg = "No se pudo guardar el usuario";

            if (error.detail) {
                msg = error.detail;
            } else if (typeof error === "object") {
                const firstKey = Object.keys(error)[0];
                if (Array.isArray(error[firstKey])) {
                    msg = error[firstKey][0];
                }
            }

            hideLoader();
            showToast(msg, "error");
            return;
        }

        modal.hide();
        await cargarUsuarios();
        showToast("Usuario guardado correctamente.");

    } catch (err) {
        showToast(err.message, "error");
    } finally {
        hideLoader();
    }
}


// =======================================================
// EDITAR
// =======================================================
async function editarUsuario(email) {
    showLoader("Cargando usuario...");

    try {
        const res = await fetch(`${API_URL}/${email}`, { headers: getHeaders() });
        if (!res.ok) throw new Error("Usuario no encontrado");

        const usuario = await res.json();
        abrirModal(usuario);

    } catch (err) {
        showToast(err.message, "error");
    } finally {
        hideLoader();
    }
}

// =======================================================
// ELIMINACIÓN (CON MODAL Y LOADER TIPO ALUMNOS)
// =======================================================

// email temporal a eliminar
let emailAEliminar = null;

// abrir modal
function confirmarEliminarUsuario(email) {
    emailAEliminar = email;

    const modalEliminar = new bootstrap.Modal(
        document.getElementById("modalConfirmarEliminarUsuario")
    );

    modalEliminar.show();
}

// botón confirmar (modal)
document.getElementById("btnConfirmarEliminarUsuario").addEventListener("click", async () => {

    if (!emailAEliminar) return;

    // pequeño delay para permitir cerrar modal antes de mostrar loader
    setTimeout(() => {
        showLoader("Eliminando usuario...");
    }, 150);

    try {
        const res = await fetch(`${API_URL}/${emailAEliminar}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (res.status !== 204) throw new Error("No se pudo eliminar");

        await cargarUsuarios();
        showToast("Usuario eliminado.");

    } catch (err) {
        showToast(err.message, "error");
    } finally {

        emailAEliminar = null;

        const modalEliminar = bootstrap.Modal.getInstance(
            document.getElementById("modalConfirmarEliminarUsuario")
        );
        modalEliminar.hide();

        hideLoader();
    }
});

// =======================================================
// INICIO
// =======================================================
cargarUsuarios();
