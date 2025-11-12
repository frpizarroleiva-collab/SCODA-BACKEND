// =============================
// CONFIG GLOBAL
// =============================
const { API_BASE_URL, SCODA_API_KEY, ACCESS_TOKEN } = window.SCODA_CONFIG || {};
const API_URL = `${API_BASE_URL}/api/usuarios`;

const token = ACCESS_TOKEN || localStorage.getItem("access_token");
if (ACCESS_TOKEN) localStorage.setItem("access_token", ACCESS_TOKEN);

function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": token ? `Bearer ${token}` : "",
        "X-API-KEY": SCODA_API_KEY,
    };
}

// =============================
// ELEMENTOS Y UTILIDADES
// =============================
const loader = document.getElementById("loader");
const loaderText = document.getElementById("loader-text");
const modal = new bootstrap.Modal(document.getElementById("modalUsuario"));

function showLoader(show, text = "Cargando...") {
    if (loaderText) loaderText.textContent = text;
    loader.style.display = show ? "flex" : "none";
}

// =============================
// CARGAR USUARIOS
// =============================
async function cargarUsuarios() {
    showLoader(true, "Cargando usuarios...");
    try {
        const res = await fetch(API_URL, { headers: getHeaders() });
        if (!res.ok) throw new Error(`Error ${res.status}`);

        const rawData = await res.json();
        const data = Array.isArray(rawData) ? rawData : rawData.results || [];

        const tbody = document.querySelector("#usuarios-table tbody");
        tbody.innerHTML = data
            .map(
                (u, i) => `
            <tr>
                <td>${i + 1}</td>
                <td>${u.first_name || ""} ${u.last_name || ""}</td>
                <td>${u.email}</td>
                <td>${u.rol}</td>
                <td>${u.is_active ? "Sí" : "No"}</td>
                <td>
                    <button class="btn btn-warning btn-sm me-1" onclick="editarUsuario('${u.email}')">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="eliminarUsuario('${u.email}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>`
            )
            .join("");
    } catch (err) {
        console.error("❌ Error al cargar usuarios:", err);
        alert("No se pudieron cargar los usuarios. Verifica token o API Key.");
    } finally {
        showLoader(false);
    }
}

// =============================
// MODAL
// =============================
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

// =============================
// GUARDAR (CREATE / UPDATE)
// =============================
async function guardarUsuario(e) {
    e.preventDefault();
    showLoader(true, "Guardando usuario...");

    const emailHidden = document.getElementById("usuarioEmailHidden").value;
    const email = document.getElementById("email").value.trim();
    const url = emailHidden ? `${API_URL}/${encodeURIComponent(emailHidden)}` : API_URL;
    const method = emailHidden ? "PUT" : "POST";

    try {
        const usuario = {
            first_name: document.getElementById("first_name").value || "SinNombre",
            last_name: document.getElementById("last_name").value || "SinApellido",
            email,
            rol: document.getElementById("rol").value,
            is_active: document.getElementById("activo").value === "true",
            password: document.getElementById("password").value || "12345678",
        };

        const res = await fetch(url, {
            method,
            headers: getHeaders(),
            body: JSON.stringify(usuario),
        });

        let data = null;
        if (res.headers.get("content-length") !== "0" && res.status !== 204) {
            try {
                data = await res.json();
            } catch {
                data = null;
            }
        }

        if (res.status === 204 || res.status === 200 || res.status === 201) {
            alert("✅ Usuario guardado correctamente.");
            modal.hide();
            await cargarUsuarios();
        } else if (!res.ok) {
            console.error("❌ Error de respuesta:", data);
            throw new Error(data?.email?.[0] || data?.detail || `Error ${res.status}`);
        }
    } catch (err) {
        console.error("⚠️ Error general:", err);
        alert(err.message || "No se pudo guardar el usuario.");
    } finally {
        showLoader(false);
    }
}

// =============================
// EDITAR
// =============================
async function editarUsuario(email) {
    showLoader(true, "Cargando usuario...");
    try {
        const res = await fetch(`${API_URL}/${encodeURIComponent(email)}`, {
            headers: getHeaders(),
        });
        if (!res.ok) throw new Error("Usuario no encontrado");
        const usuario = await res.json();
        abrirModal(usuario);
    } catch (err) {
        alert("No se pudo obtener el usuario: " + err.message);
    } finally {
        showLoader(false);
    }
}

// =============================
// ELIMINAR
// =============================
async function eliminarUsuario(email) {
    if (!confirm("¿Seguro que deseas eliminar este usuario?")) return;

    showLoader(true, "Eliminando usuario...");
    try {
        const res = await fetch(`${API_URL}/${encodeURIComponent(email)}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (res.status === 204) {
            alert("Usuario eliminado correctamente.");
            await cargarUsuarios();
        } else {
            const data = await res.json();
            throw new Error(data?.detail || "Error al eliminar usuario.");
        }
    } catch (err) {
        alert(err.message);
    } finally {
        showLoader(false);
    }
}

// =============================
// VOLVER AL DASHBOARD
// =============================
function volverDashboard() {
    window.location.href = "/panel/dashboard/";
}

// =============================
// INICIALIZACIÓN
// =============================
cargarUsuarios();
