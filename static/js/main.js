// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(a => {
        setTimeout(() => {
            a.style.transition = 'opacity 0.4s';
            a.style.opacity = '0';
            setTimeout(() => a.remove(), 400);
        }, 4000);
    });

    // Notification bell toggle
    const bell = document.getElementById('notifBell');
    if (bell) {
        bell.addEventListener('click', (e) => {
            e.stopPropagation();
            const panel = document.getElementById('notifPanel');
            if (panel) panel.classList.toggle('open');
        });
        document.addEventListener('click', () => {
            const panel = document.getElementById('notifPanel');
            if (panel) panel.classList.remove('open');
        });
    }
});
