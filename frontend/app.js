// Espera a que todo el contenido del HTML se cargue antes de ejecutar el script
document.addEventListener('DOMContentLoaded', () => {
    
    console.log("¡JavaScript está cargado!");

    // Esta es la URL de nuestro "cerebro" (el backend de Flask)
    const API_URL = "http://127.0.0.1:5000";

    // Hacemos nuestra primera petición "fetch" al endpoint de "Hola, mundo"
    fetch(API_URL + "/")
        .then(response => response.text()) // Convertimos la respuesta a texto plano
        .then(data => {
            // Si todo sale bien, mostramos el dato en la consola
            console.log("Respuesta del backend:", data);
        })
        .catch(error => {
            // Si hay un error (ej. el backend no está corriendo), lo mostramos
            console.error("¡Error al conectar con el backend!:", error);
        });

});