// Esperamos a que todo el HTML cargue antes de ejecutar el script
document.addEventListener("DOMContentLoaded", () => {
    
    // Seleccionamos todos los botones de "Copiar código"
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(button => {
        button.addEventListener('click', async () => {
            // Buscamos el contenedor principal de este botón
            const wrapper = button.closest('.code-block-wrapper');
            // Dentro de ese contenedor, buscamos la etiqueta que tiene el código
            const codeBlock = wrapper.querySelector('code');
            
            try {
                // Copiamos el texto al portapapeles del usuario
                await navigator.clipboard.writeText(codeBlock.innerText);
                
                // Efecto visual: Cambiamos el texto y el color temporalmente
                const originalText = button.innerText;
                button.innerText = '¡Copiado!';
                button.style.color = '#10b981'; // Verde neón (tu color de acento)
                button.style.borderColor = '#10b981';
                
                // Regresamos el botón a la normalidad después de 2 segundos
                setTimeout(() => {
                    button.innerText = originalText;
                    button.style.color = '';
                    button.style.borderColor = '';
                }, 2000);
                
            } catch (err) {
                console.error('Error al copiar: ', err);
                button.innerText = 'Error al copiar';
            }
        });
    });

});