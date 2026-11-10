/* ═══════════════════════════════════════
   OmborTizim — Main JavaScript
   ═══════════════════════════════════════ */

// ─── Theme Toggle ───
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Save via cookie for Django to read initially
    document.cookie = `dark_mode=${newTheme === 'dark' ? '1' : '0'}; path=/; max-age=31536000`;

    // Save to user profile via AJAX
    fetch('/toggle-theme/')
        .then(response => response.json())
        .catch(console.error);
}

// Load saved theme
(function () {
    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }
})();

// ─── Sidebar Toggle ───
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Close sidebar on click outside (mobile)
document.addEventListener('click', function (e) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if (sidebar && toggle && window.innerWidth <= 1024) {
        if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});

// ─── Auto-dismiss alerts ───
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// ─── Number formatting ───
function formatNumber(num) {
    return new Intl.NumberFormat('uz-UZ').format(num);
}

// ─── Confirm delete ───
function confirmDelete(message) {
    return confirm(message || "Haqiqatan ham o'chirmoqchimisiz?");
}

// ─── Animate numbers ───
function animateValue(element, start, end, duration) {
    if (start === end) {
        element.textContent = formatNumber(end);
        return;
    }
    const range = end - start;
    let current = start;
    const stepTime = Math.abs(Math.floor(duration / range));
    const timer = setInterval(function () {
        current += Math.sign(range);
        element.textContent = formatNumber(current);
        if (current === end) {
            clearInterval(timer);
        }
    }, Math.max(stepTime, 1));
}

// ─── Smooth page transitions ───
document.addEventListener('DOMContentLoaded', function () {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease';
    requestAnimationFrame(function () {
        document.body.style.opacity = '1';
    });

    // Fetch notifications
    fetchNotifications();
    setInterval(fetchNotifications, 60000); // har daqiqada
});

// Notifications
function toggleNotifications() {
    const box = document.getElementById('notiBox');
    if (box.style.display === 'none' || !box.style.display) {
        box.style.display = 'flex';
    } else {
        box.style.display = 'none';
    }
}

function fetchNotifications() {
    fetch('/api/notifications/')
        .then(res => res.json())
        .then(data => {
            const dot = document.getElementById('notiDot');
            const list = document.getElementById('notiList');
            const count = document.getElementById('notiCount');

            if (!dot || !list || !count) return;

            count.textContent = data.count;
            if (data.count > 0) {
                dot.style.display = 'block';
                list.innerHTML = '';
                data.notifications.forEach(n => {
                    let color = n.type === 'danger' ? 'var(--danger)' : 'var(--warning)';
                    list.innerHTML += `
                        <a href="${n.url}" style="display:block; padding:12px 16px; border-bottom:1px solid var(--border); text-decoration:none; color:inherit; transition:0.2s;" onmouseover="this.style.background='var(--surface-hover)'" onmouseout="this.style.background='transparent'">
                            <div style="font-size:12px; font-weight:700; color:${color}; margin-bottom:4px;">${n.title}</div>
                            <div style="font-size:12px;">${n.message}</div>
                        </a>
                    `;
                });
            } else {
                dot.style.display = 'none';
                list.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted); font-size:12px;">Yangi xabarlar yo'q</div>`;
            }
        }).catch(err => console.error(err));
}

// Click outside to close notification box
document.addEventListener('click', function (e) {
    const box = document.getElementById('notiBox');
    const dropdown = document.getElementById('notificationDropdown');
    if (box && dropdown && !dropdown.contains(e.target)) {
        box.style.display = 'none';
    }
});
