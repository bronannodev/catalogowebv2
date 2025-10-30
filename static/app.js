document.addEventListener('DOMContentLoaded', () => {

    // --- Lógica de Login (Esta la maneja 'index.html' en su script) ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        // ... (el 'index.html' tiene su propio script para el modal de login)
        // ... (dejamos esto aquí por si lo usas en otra página)
    }

    // --- Lógica de Registro (¡MODIFICADA!) ---
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const secret_key = document.getElementById('secret_key').value.trim();
            // const message = document.getElementById('message'); // Ya no lo usamos

            if (!username || !password || !secret_key) {
                // CAMBIO: Reemplaza alerta de texto por SweetAlert
                Swal.fire({
                    icon: 'warning',
                    title: 'Campos incompletos',
                    text: 'Por favor, completa todos los campos.'
                });
                return;
            }

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, secret_key })
                });

                const result = await response.json();

                if (response.ok) {
                    // CAMBIO: Reemplaza alerta de texto por SweetAlert
                    Swal.fire({
                        icon: 'success',
                        title: '¡Éxito!',
                        text: 'Usuario creado. Redirigiendo al login...',
                        timer: 2000,
                        showConfirmButton: false,
                        willClose: () => {
                            window.location.href = '/'; // Redirige al login
                        }
                    });
                } else {
                    // CAMBIO: Reemplaza alerta de texto por SweetAlert
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: result.error // 'error' viene de tu app.py
                    });
                }
            } catch (error) {
                // CAMBIO: Reemplaza alerta de texto por SweetAlert
                Swal.fire({
                    icon: 'error',
                    title: 'Error de conexión',
                    text: 'No se pudo conectar con el servidor.'
                });
            }
        });
    }

    // --- Lógica de Logout (¡MODIFICADA!) ---
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                await fetch('/api/logout');
                window.location.href = '/';
            } catch (err) {
                // CAMBIO: Reemplaza alert() por SweetAlert
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo cerrar la sesión.'
                });
            }
        });
    }
});