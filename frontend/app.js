// Espera a que todo el contenido del HTML se cargue
document.addEventListener('DOMContentLoaded', () => {
    
    // --- Constantes ---
    const API_URL = "http://127.0.0.1:5000"; // URL de nuestro backend

    // --- Selectores del DOM ---
    const authContainer = document.getElementById('auth-container');
    const userDashboard = document.getElementById('user-dashboard');
    const welcomeMessage = document.getElementById('welcome-message');
    const logoutButton = document.getElementById('logout-button');
    
    const registerForm = document.getElementById('register-form');
    const registerMessage = document.getElementById('register-message');
    const loginForm = document.getElementById('login-form');
    const loginMessage = document.getElementById('login-message');

    // --- Estado de la Aplicación ---
    checkLoginStatus();

    // --- Funciones ---

    /**
     * Función principal que se ejecuta al cargar la página.
     * Revisa si hay un token en localStorage para decidir qué mostrar.
     */
    async function checkLoginStatus() {
        const token = localStorage.getItem('access_token');

        if (token) {
            // Si hay token, intentamos obtener el perfil del usuario
            try {
                const user = await fetchUserProfile(token);
                // Si el token es válido y obtenemos el usuario:
                showDashboard(user.username);
            } catch (error) {
                // Si el token es inválido o expiró:
                console.warn("Token inválido o expirado. Mostrando login.");
                showAuthForms();
                localStorage.removeItem('access_token'); // Limpiar token malo
            }
        } else {
            // Si no hay token:
            showAuthForms();
        }
    }

    /**
     * Muestra el dashboard y oculta los formularios de autenticación.
     */
    function showDashboard(username) {
        authContainer.classList.add('hidden');
        userDashboard.classList.remove('hidden');
        welcomeMessage.textContent = `¡Bienvenido, ${username}!`;
    }

    /**
     * Muestra los formularios de autenticación y oculta el dashboard.
     */
    function showAuthForms() {
        authContainer.classList.remove('hidden');
        userDashboard.classList.add('hidden');

        // Limpiamos cualquier mensaje de éxito o error anterior. O sea, el parrafo de éxito o fracaso
    if (loginMessage) loginMessage.textContent = '';
    if (registerMessage) registerMessage.textContent = '';
    }

    /**
     * (¡NUEVA!) Hace una petición GET a la API protegida /api/profile
     * para verificar el token y obtener los datos del usuario.
     */
    async function fetchUserProfile(token) {
        const response = await fetch(API_URL + '/api/profile', {
            method: 'GET',
            headers: {
                // ¡AQUÍ USAMOS EL PASE VIP!
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Falló la obtención del perfil');
        }
        return await response.json(); // Devuelve los datos del usuario (id, username, email)
    }

    // --- Event Listeners (Oyentes de eventos) ---

    // Lógica de Registro (sin cambios, solo la pegamos aquí)
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

    // Lógica de Login (la adaptamos un poco)
    if (loginForm) {
        // 1. Escuchar el evento "submit" del formulario
        loginForm.addEventListener('submit', async (event) => {
            // 2. Prevenir la recarga de la página
            event.preventDefault();
            // ... (el resto de tu código de fetch de login va aquí) ...
            // Pega tu código de la Misión #26 aquí

            // SOLO ASEGÚRATE de que en la parte de "if (response.ok)"
            // llames a la nueva función para mostrar el dashboard:
            //
            // if (response.ok) {
            //     localStorage.setItem('access_token', data.access_token);
            //     showDashboard(data.usuario.username); // <-- ¡LLAMAR A ESTA FUNCIÓN!
            // } else {
            //     ...
            // }

             // 3. Obtener los valores
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            const loginData = {
                email: email,
                password: password
            };

            // 5. Enviar los datos al backend
            try {
                const response = await fetch(API_URL + '/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(loginData)
                });

                const data = await response.json();

                if (response.ok) {
                    // ¡ÉXITO!
                    loginMessage.textContent = data.mensaje;
                    loginMessage.style.color = 'green';
                    
                    // --- ¡LO MÁS IMPORTANTE! ---
                    // Guardamos el token en el "almacén local" del navegador
                    localStorage.setItem('access_token', data.access_token);

                    loginForm.reset();
                    
                    // (En un futuro, aquí redirigiríamos al usuario a otra página)
                    console.log("Token guardado:", data.access_token); //localStorage es un pequeño "almacén" que tiene el navegador. Le estamos diciendo: "Guarda este access_token y no lo borres aunque el usuario cierre la pestaña". Así, podemos usar este "pase VIP" en el futuro para otras peticiones.
                    showDashboard(data.usuario.username);

                } else {
                    // Error (ej. 401 Unauthorized)
                    loginMessage.textContent = 'Error: ' + data.error;
                    loginMessage.style.color = 'red';
                }

            } catch (error) {
                // Error de red
                console.error('Error de red al iniciar sesión:', error);
                loginMessage.textContent = 'Error de conexión. Inténtalo más tarde.';
                loginMessage.style.color = 'red';
            }
        });
    }
    
    // (¡NUEVO!) Lógica de Cerrar Sesión
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('access_token'); // Borra el token
            showAuthForms(); // Muestra los formularios de login/registro
            console.log("Sesión cerrada.");
        });
    }

});