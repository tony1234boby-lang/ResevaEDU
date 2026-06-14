// push_notifications.js
// Handles Web Audio synthesis, Vibration, System Notifications, and Fullscreen alerts on new invitations.

function reproducirSonidoNotificacion() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        // Tone 1
        const osc1 = audioCtx.createOscillator();
        const gain1 = audioCtx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
        gain1.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        osc1.connect(gain1);
        gain1.connect(audioCtx.destination);
        osc1.start();
        osc1.stop(audioCtx.currentTime + 0.3);
        
        // Tone 2
        setTimeout(() => {
            const osc2 = audioCtx.createOscillator();
            const gain2 = audioCtx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(659.25, audioCtx.currentTime); // E5
            gain2.gain.setValueAtTime(0.3, audioCtx.currentTime);
            gain2.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
            osc2.connect(gain2);
            gain2.connect(audioCtx.destination);
            osc2.start();
            osc2.stop(audioCtx.currentTime + 0.4);
        }, 150);
    } catch (e) {
        console.warn('AudioContext not allowed or not supported:', e);
    }
}

function mostrarNotificacionPantallaCompleta(n) {
    // Vibrate phone
    if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200, 100, 300]);
    }
    
    // Play ping sound
    reproducirSonidoNotificacion();

    // Create modal element
    const modal = document.createElement('div');
    modal.id = `fs-notif-modal-${n.id}`;
    modal.className = 'fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md transition-all duration-300';
    
    modal.innerHTML = `
        <div class="bg-white max-w-lg w-full rounded-[2.5rem] p-8 shadow-2xl relative border border-slate-100 flex flex-col items-center text-center transform scale-95 opacity-0 transition-all duration-300" id="fs-notif-content-${n.id}">
            <button onclick="cerrarNotificacionPantallaCompleta(${n.id})" class="absolute top-6 right-6 z-10 w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center hover:bg-slate-200 transition-colors border-none cursor-pointer">
                <span class="material-symbols-outlined text-sm">close</span>
            </button>

            <!-- Wave effect icon -->
            <div class="relative w-24 h-24 mb-6 flex items-center justify-center">
                <div class="absolute inset-0 rounded-full bg-primary/10 animate-ping opacity-75"></div>
                <div class="absolute inset-2 rounded-full bg-primary/20 animate-pulse"></div>
                <div class="w-16 h-16 rounded-full bg-primary text-white flex items-center justify-center shadow-lg relative z-10">
                    <span class="material-symbols-outlined text-3xl" style="font-variation-settings: 'FILL' 1">notifications_active</span>
                </div>
            </div>
            
            <span class="text-[10px] font-black text-primary uppercase tracking-widest px-4 py-1.5 bg-blue-50 border border-blue-100 rounded-full mb-4">Nueva Invitación Recibida</span>
            
            <h2 class="text-2xl font-black text-slate-800 mb-4 tracking-tight leading-tight">Tienes una Notificación</h2>
            <p class="text-sm text-slate-600 leading-relaxed mb-6 font-medium px-4">${n.mensaje}</p>
            
            <div class="w-full bg-slate-50 border border-slate-100 p-5 rounded-2xl mb-8 flex flex-col gap-3 text-left text-xs font-semibold text-slate-500">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-sm text-slate-400">meeting_room</span>
                    <span>Espacio: <strong class="text-slate-700">${n.espacio}</strong></span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-sm text-slate-400">calendar_month</span>
                    <span>Fecha: <strong class="text-slate-700">${n.fecha}</strong></span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-sm text-slate-400">schedule</span>
                    <span>Horario: <strong class="text-slate-700">${n.horario}</strong></span>
                </div>
            </div>
            
            <button onclick="cerrarNotificacionPantallaCompleta(${n.id})" 
                class="w-full bg-primary hover:bg-primary-dark text-white py-4 rounded-2xl font-bold text-xs uppercase tracking-widest transition-all shadow-lg hover:shadow-xl active:scale-[0.98] cursor-pointer border-none">
                Entendido
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Animate content scale-in
    setTimeout(() => {
        const mc = document.getElementById(`fs-notif-content-${n.id}`);
        if (mc) {
            mc.classList.replace('scale-95', 'scale-100');
            mc.classList.replace('opacity-0', 'opacity-100');
        }
    }, 50);
}

function cerrarNotificacionPantallaCompleta(id) {
    const modal = document.getElementById(`fs-notif-modal-${id}`);
    const mc = document.getElementById(`fs-notif-content-${id}`);
    if (modal && mc) {
        mc.classList.replace('scale-100', 'scale-95');
        mc.classList.replace('opacity-100', 'opacity-0');
        setTimeout(() => modal.remove(), 300);
    }
}

// Polling function for new notifications
async function checkNewNotifications() {
    try {
        const response = await fetch('/api/notificaciones/nuevas/');
        if (!response.ok) return;
        const data = await response.json();
        
        if (data.nuevas && data.nuevas.length > 0) {
            data.nuevas.forEach(n => {
                // 1. Show System Notification (if browser/Capacitor allows)
                if (window.Notification && Notification.permission === "granted") {
                    new Notification("ReservaEDU - Nueva Invitación", {
                        body: n.mensaje,
                        icon: "/static/images/escudo_dolorosa.jpg"
                    });
                }
                
                // 2. Show Fullscreen Overlay Notification
                mostrarNotificacionPantallaCompleta(n);
                
                // 3. Update the bell notification count dynamically in the header
                const countBadge = document.querySelector('.absolute.-top-1.5.-right-1.5, #avatar-initials + span, .bg-red-500');
                if (countBadge) {
                    const currentCount = parseInt(countBadge.innerText) || 0;
                    countBadge.innerText = currentCount + 1;
                    countBadge.classList.remove('hidden');
                }
            });
        }
    } catch (error) {
        console.warn('Error fetching new notifications:', error);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    // Request permission for system notifications
    if (window.Notification && Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
    }
    
    // Poll every 5 seconds
    setInterval(checkNewNotifications, 5000);

    // Detect mobile app environment
    const isApp = window.Capacitor || navigator.userAgent.includes('ReservaEDUMobile');
    if (isApp) {
        document.body.classList.add('is-app');
        
        // Hide user greeting (e.g. "¡Hola, TONY!")
        document.querySelectorAll('span').forEach(el => {
            if (el.textContent && el.textContent.includes('¡Hola,')) {
                el.classList.add('app-hide');
            }
        });
        
        // Hide top navigation tab buttons on content pages if present
        const spacesBtn = document.getElementById('top-btn-spaces');
        if (spacesBtn) {
            const parentContainer = spacesBtn.closest('div.flex-wrap');
            if (parentContainer) {
                const outerWrapper = parentContainer.closest('div.w-full.pb-4');
                if (outerWrapper) {
                    outerWrapper.classList.add('app-hide');
                } else {
                    parentContainer.classList.add('app-hide');
                }
            }
        }
        
        // Setup dynamic styles for the app
        const style = document.createElement('style');
        style.textContent = `
            body.is-app {
                padding-left: 0 !important;
            }
            body.is-app .app-hide {
                display: none !important;
            }
            body.is-app aside {
                display: flex !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                bottom: 0 !important;
                height: 100vh !important;
                z-index: 150 !important;
                transform: translateX(-100%) !important;
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            body.is-app aside.open {
                transform: translateX(0) !important;
                box-shadow: 5px 0 25px rgba(0, 0, 0, 0.2) !important;
            }
            #sidebar-overlay {
                position: fixed;
                inset: 0;
                background: rgba(15, 23, 42, 0.4);
                backdrop-filter: blur(4px);
                z-index: 140;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.3s ease;
            }
            body.is-app.sidebar-open #sidebar-overlay {
                opacity: 1;
                pointer-events: auto;
            }
            #app-hamburger-btn {
                background: transparent;
                border: none;
                color: #1e40af;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 8px;
                border-radius: 8px;
                margin-right: 12px;
                transition: background 0.2s;
            }
            #app-hamburger-btn:hover {
                background: rgba(30, 64, 175, 0.05);
            }
        `;
        document.head.appendChild(style);
        
        // Add overlay to body
        const overlay = document.createElement('div');
        overlay.id = 'sidebar-overlay';
        document.body.appendChild(overlay);
        overlay.onclick = () => {
            const sidebar = document.querySelector('aside');
            if (sidebar) {
                sidebar.classList.remove('open');
                document.body.classList.remove('sidebar-open');
            }
        };
        
        // Prepend hamburger button to header
        const header = document.querySelector('header');
        if (header) {
            const burgerBtn = document.createElement('button');
            burgerBtn.id = 'app-hamburger-btn';
            burgerBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 26px;">menu</span>';
            header.prepend(burgerBtn);
            
            burgerBtn.onclick = (e) => {
                e.stopPropagation();
                const sidebar = document.querySelector('aside');
                if (sidebar) {
                    sidebar.classList.toggle('open');
                    document.body.classList.toggle('sidebar-open');
                }
            };
        }
        
        // Convert nav-spaces link to call switchView dynamically on homepage
        const navSpaces = document.getElementById('nav-spaces');
        if (navSpaces && typeof switchView === 'function') {
            navSpaces.removeAttribute('href');
            navSpaces.setAttribute('onclick', "switchView('spaces')");
        }
        
        // Add LA DOLO to sidebar nav if available
        const nav = document.querySelector('aside nav');
        if (nav && typeof toggleAIChat === 'function' && !document.getElementById('nav-ladolo')) {
            const laDoloLink = document.createElement('a');
            laDoloLink.id = 'nav-ladolo';
            laDoloLink.className = 'flex items-center gap-3 px-4 py-3 text-slate-500 hover:bg-slate-200/50 rounded-xl cursor-pointer transition-all';
            laDoloLink.onclick = () => {
                toggleAIChat();
                const sidebar = document.querySelector('aside');
                if (sidebar) {
                    sidebar.classList.remove('open');
                    document.body.classList.remove('sidebar-open');
                }
            };
            laDoloLink.innerHTML = `
                <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1">auto_awesome</span>
                <span class="font-bold">LA DOLO</span>
            `;
            nav.appendChild(laDoloLink);
        }
        
        // Close sidebar drawer when clicking links inside it
        document.querySelectorAll('aside nav a, aside .mt-auto a, aside nav button, aside .mt-auto button').forEach(link => {
            link.addEventListener('click', () => {
                const sidebar = document.querySelector('aside');
                if (sidebar) {
                    sidebar.classList.remove('open');
                    document.body.classList.remove('sidebar-open');
                }
            });
        });
    }
});
