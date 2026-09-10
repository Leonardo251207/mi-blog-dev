document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. LÓGICA DE COPIAR CÓDIGO ---
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const wrapper = button.closest('.code-block-wrapper');
            const codeBlock = wrapper.querySelector('code');
            
            try {
                await navigator.clipboard.writeText(codeBlock.innerText);
                
                const originalText = button.innerText;
                button.innerText = '¡Copiado!';
                button.style.color = '#10b981'; 
                button.style.borderColor = '#10b981';
                
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

    // --- 2. LÓGICA DEL SIMULADOR DE TERMINAL ---
    const runBtn = document.getElementById('run-simulator');
    const terminalOutput = document.getElementById('terminal-output');

    if (runBtn && terminalOutput) {
        const events = [
            "> Detectado: 'apuntes_calculo.pdf'",
            "> Analizando contenido con IA...",
            "> Categoría identificada: Matemáticas",
            "> Moviendo a: /Universidad/Cuatri_3/Matematicas/",
            "[ÉXITO] Archivo organizado correctamente.",
            " ",
            "> Esperando nuevos archivos..."
        ];

        runBtn.addEventListener('click', () => {
            terminalOutput.innerHTML = '';
            runBtn.disabled = true;
            runBtn.innerText = 'Ejecutando...';
            
            let i = 0;
            const interval = setInterval(() => {
                if (i < events.length) {
                    const line = document.createElement('span');
                    line.className = 'terminal-line';
                    
                    if (events[i].includes('[ÉXITO]')) {
                        line.style.color = '#10b981';
                    }
                    
                    line.innerText = events[i];
                    terminalOutput.appendChild(line);
                    i++;
                } else {
                    clearInterval(interval);
                    runBtn.disabled = false;
                    runBtn.innerText = '▶ Ejecutar Script';
                }
            }, 800); 
        });
    }

    // --- 3. ANIMACIONES DE ENTRADA (SCROLL) ---
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15
    };

    const scrollObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const elementsToAnimate = document.querySelectorAll(`
        .card, 
        .article-hero-img, 
        .content-body > p, 
        .content-body > h3, 
        .content-body > blockquote, 
        .code-block-wrapper, 
        .table-responsive, 
        .simulator-box
    `);
    
    elementsToAnimate.forEach((el, index) => {
        el.classList.add('fade-in-up');
        
        if (el.classList.contains('card')) {
            el.style.transitionDelay = `${index * 0.15}s`;
        } else {
            el.style.transitionDelay = '0s';
        }
        
        scrollObserver.observe(el);
    });

});