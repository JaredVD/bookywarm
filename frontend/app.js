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

    // --- Selectores del DOM (Búsqueda) (NUEVO) ---
    const searchForm = document.getElementById('search-form');
    const searchQuery = document.getElementById('search-query');
    const searchResults = document.getElementById('search-results');

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

    if (loginMessage) loginMessage.textContent = '';
    if (registerMessage) registerMessage.textContent = '';
    
    // Limpiamos cualquier mensaje de éxito o error anterior. O sea, el parrafo de éxito o fracaso
    if (loginMessage) loginMessage.textContent = '';
    if (registerMessage) registerMessage.textContent = '';

    // Limpiamos los resultados de búsqueda y el texto del input.
    if (searchResults) searchResults.innerHTML = '';
    if (searchQuery) searchQuery.value = '';

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


    /**
     * (NUEVA) Maneja el envío del formulario de búsqueda.
     */
    async function handleSearchSubmit(event) {
        event.preventDefault();
        const query = searchQuery.value.trim(); // Obtener el texto y quitar espacios
        
        if (!query) {
            searchResults.innerHTML = '<p class="message" style="color: red;">Por favor, escribe un término de búsqueda.</p>';
            return;
        }

        searchResults.innerHTML = '<p class="message">Buscando...</p>'; // Mensaje de carga

        try {
            const token = localStorage.getItem('access_token');
            // Nota: La API de búsqueda de Google no requiere nuestro token,
            // pero en un futuro podríamos querer proteger este endpoint.
            // Por ahora, no es estrictamente necesario enviar el token.
            
            const response = await fetch(`${API_URL}/api/books/search?q=${query}`, {
                method: 'GET',
                headers: {
                    // Si el endpoint estuviera protegido, añadiríamos la autorización:
                    // 'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Error en la búsqueda');
            }

            const books = await response.json(); // La lista de libros
            renderSearchResults(books);

        } catch (error) {
            console.error('Error al buscar libros:', error);
            searchResults.innerHTML = '<p class="message" style="color: red;">Error al buscar. Inténtalo más tarde.</p>';
        }
    }

    /**
     * (NUEVA) Dibuja los resultados de la búsqueda en el HTML.
     */
    function renderSearchResults(books) {
        // Limpiar resultados anteriores
        searchResults.innerHTML = '';

        if (books.length === 0) {
            searchResults.innerHTML = '<p class="message">No se encontraron libros para esa búsqueda.</p>';
            return;
        }

        // Crear una "tarjeta" por cada libro
        books.forEach(book => {
            const bookCard = document.createElement('div');
            bookCard.className = 'book-card';

            // Usar una imagen genérica si no hay portada
            const coverImage = book.cover_image ? book.cover_image : 'https.via.placeholder.com/80x120.png?text=No+Cover';
            
            // Limitar la descripción
            const description = book.description ? book.description.substring(0, 150) + '...' : 'No hay descripción disponible.';

            bookCard.innerHTML = `
                <img src="${coverImage}" alt="Portada de ${book.title}">
                <div class="book-card-info">
                    <h4>${book.title}</h4>
                    <p><strong>Autor(es):</strong> ${book.authors ? book.authors.join(', ') : 'Desconocido'}</p>
                    <p>${description}</p>
                </div>
                <div class="book-card-actions">
                    <div class="rating-input">
                        <label for="rating-${book.google_books_id}">Calificación:</label>
                        <select id="rating-${book.google_books_id}">
                            <option value="1">1 ★</option>
                            <option value="2">2 ★</option>
                            <option value="3">3 ★</option>
                            <option value="4">4 ★</option>
                            <option value="5" selected>5 ★</option>
                        </select>
                    </div>
                    <button class="save-book-btn" 
                            data-google-id="${book.google_books_id}"
                            data-title="${book.title}"
                            data-author="${book.authors ? book.authors.join(', ') : 'Desconocido'}">
                        Guardar en mi lista
                    </button>
                </div>
            `;
            searchResults.appendChild(bookCard);
        });
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

    // (NUEVO) Lógica de Búsqueda
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }

});