// Espera a que todo el contenido del HTML se cargue
document.addEventListener('DOMContentLoaded', () => {
    
    // --- Constantes ---
    const API_URL = "http://127.0.0.1:5000"; // URL de nuestro backend

    // --- Selectores del DOM (Formulario de Registro) ---
    const registerForm = document.getElementById('register-form');
    const registerMessage = document.getElementById('register-message');

    // --- Lógica de Registro ---
    if (registerForm) {
        // 1. Escuchar el evento "submit" (envío) del formulario
        registerForm.addEventListener('submit', async (event) => {
            
            // 2. Prevenir el comportamiento por defecto (que recarga la página)
            event.preventDefault();

            // 3. Obtener los valores de los campos del formulario
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;

            // 4. Crear el objeto de datos para enviar (debe coincidir con la API)
            const userData = {
                username: username,
                email: email,
                password: password
            };

            // 5. Enviar los datos al backend usando fetch
            try {
                const response = await fetch(API_URL + '/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json' // Avisamos que enviamos JSON
                    },
                    body: JSON.stringify(userData) // Convertimos el objeto a un string JSON
                });

                const data = await response.json(); // Convertimos la respuesta del servidor a un objeto

                if (response.ok) {
                    // response.ok es true si el status es 200-299 (ej. 201 Created)
                    registerMessage.textContent = data.mensaje;
                    registerMessage.style.color = 'green';
                    registerForm.reset(); // Limpiar el formulario
                    
                } else {
                    // Si el servidor devuelve un error (ej. 409 Conflict)
                    registerMessage.textContent = 'Error: ' + data.error;
                    registerMessage.style.color = 'red';
                    
                }

            } catch (error) {
                // Si hay un error de red (ej. el backend está apagado)
                console.error('Error de red al registrar:', error);
                registerMessage.textContent = 'Error de conexión. Inténtalo más tarde.';
                registerMessage.style.color = 'red';
            }
        });
    }

});