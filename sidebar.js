/**
 * TRẦN THÀNH MMO HUB - SIDEBAR COMPONENT (DÙNG CHUNG)
 */

// 1. Kiểm tra đăng nhập
const loggedUser = localStorage.getItem('hub_logged_username');
if (!loggedUser && !window.location.pathname.endsWith("index.html") && window.location.pathname !== "/") {
    window.location.href = "index.html";
}

// 2. Danh sách Menu
const MENU_ITEMS = [
    { name: "TRANG CHỦ", href: "home.html", icon: "fa-solid fa-house" },
    { name: "AIRDROP", href: "airdrop.html", icon: "fa-solid fa-parachute-box" },
    { name: "APP & EXTENSION", href: "tools.html", icon: "fa-solid fa-puzzle-piece" },
    { name: "TÀI NGUYÊN", href: "resources.html", icon: "fa-solid fa-box-archive" },
    { name: "DỊCH VỤ PROXY", href: "proxy.html", icon: "fa-solid fa-network-wired" },
    { name: "LICENSE SCRIPT", href: "license.html", icon: "fa-solid fa-key" }
];

function initHubSidebar() {
    const sidebarMount = document.getElementById('hubSidebarMount');
    if (!sidebarMount) return;

    const currentPath = window.location.pathname.split("/").pop() || "home.html";
    const isCollapsed = localStorage.getItem('hub_sidebar_collapsed') === 'true';

    sidebarMount.innerHTML = `
        <aside id="hubSidebar" class="${isCollapsed ? 'w-20' : 'w-64'} bg-white border-r border-slate-200 flex flex-col justify-between h-screen sticky top-0 shrink-0 p-3 transition-all duration-300 relative z-30">
            
            <!-- Nút thu gọn / mở rộng -->
            <button onclick="toggleSidebarCollapse()" id="btnCollapse" title="Thu gọn / Mở rộng" 
                class="absolute -right-3.5 top-6 w-7 h-7 bg-white border border-slate-200 text-blue-600 rounded-full shadow-md flex items-center justify-center text-xs hover:bg-blue-50 transition z-40">
                <i id="collapseIcon" class="fa-solid ${isCollapsed ? 'fa-angles-right' : 'fa-angles-left'}"></i>
            </button>

            <!-- Menu bên trên -->
            <div>
                <div class="flex items-center gap-3 px-1.5 py-3 mb-5 border-b border-slate-100 overflow-hidden">
                    <img src="logo.png" alt="Logo" class="w-10 h-10 rounded-2xl object-cover shadow-sm border border-slate-200 shrink-0">
                    <div class="sidebar-text truncate ${isCollapsed ? 'hidden' : ''}">
                        <h1 class="text-sm font-black text-slate-900 tracking-tight truncate">TRẦN THÀNH HUB</h1>
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">MMO & Crypto Hub</p>
                    </div>
                </div>

                <nav class="space-y-1.5 font-bold text-xs">
                    ${MENU_ITEMS.map(item => {
                        const isActive = currentPath === item.href || (currentPath === '' && item.href === 'home.html');
                        return `
                            <a href="${item.href}" title="${item.name}" 
                               class="flex items-center gap-3.5 px-3 py-3 rounded-2xl transition overflow-hidden ${isActive ? 'bg-blue-50 text-blue-600 font-black shadow-sm' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}">
                                <i class="${item.icon} w-5 text-center text-sm shrink-0"></i>
                                <span class="sidebar-text truncate ${isCollapsed ? 'hidden' : ''}">${item.name}</span>
                            </a>
                        `;
                    }).join('')}
                </nav>
            </div>

            <!-- Avatar & Nút bấm chuyển sang trang Profile -->
            <div class="pt-3 border-t border-slate-100 relative">
                <button onclick="toggleUserDropdown()" class="w-full flex items-center justify-between p-1.5 rounded-2xl hover:bg-slate-50 transition overflow-hidden">
                    <div class="flex items-center gap-2.5 truncate">
                        <div class="w-9 h-9 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center font-black text-sm shrink-0">
                            <i class="fa-solid fa-user"></i>
                        </div>
                        <div class="sidebar-text text-left truncate ${isCollapsed ? 'hidden' : ''}">
                            <p class="text-xs font-black text-slate-900 truncate">${loggedUser || 'Member'}</p>
                            <p class="text-[10px] text-emerald-600 font-bold">Active Member</p>
                        </div>
                    </div>
                    <i class="sidebar-text fa-solid fa-ellipsis-vertical text-slate-400 text-xs px-1 ${isCollapsed ? 'hidden' : ''}"></i>
                </button>

                <!-- Menu popup -->
                <div id="userMenuPopup" class="hidden absolute bottom-16 left-0 w-48 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50">
                    <a href="profile.html" class="w-full text-left px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 flex items-center gap-2">
                        <i class="fa-solid fa-user-gear text-blue-600"></i> Quản Lý Tài Khoản
                    </a>
                    <button onclick="logoutNow()" class="w-full text-left px-4 py-2.5 text-xs font-bold text-rose-600 hover:bg-rose-50 flex items-center gap-2">
                        <i class="fa-solid fa-right-from-bracket"></i> Đăng xuất
                    </button>
                </div>
            </div>

        </aside>
    `;
}

function toggleSidebarCollapse() {
    const sidebar = document.getElementById('hubSidebar');
    const collapseIcon = document.getElementById('collapseIcon');
    const texts = document.querySelectorAll('.sidebar-text');
    const willCollapse = !sidebar.classList.contains('w-20');
    
    if (willCollapse) {
        sidebar.classList.remove('w-64');
        sidebar.classList.add('w-20');
        collapseIcon.classList.remove('fa-angles-left');
        collapseIcon.classList.add('fa-angles-right');
        texts.forEach(t => t.classList.add('hidden'));
        localStorage.setItem('hub_sidebar_collapsed', 'true');
    } else {
        sidebar.classList.remove('w-20');
        sidebar.classList.add('w-64');
        collapseIcon.classList.remove('fa-angles-right');
        collapseIcon.classList.add('fa-angles-left');
        texts.forEach(t => t.classList.remove('hidden'));
        localStorage.setItem('hub_sidebar_collapsed', 'false');
    }
}

function toggleUserDropdown() {
    const popup = document.getElementById('userMenuPopup');
    if (popup) popup.classList.toggle('hidden');
}

document.addEventListener('click', (e) => {
    const popup = document.getElementById('userMenuPopup');
    if (popup && !popup.contains(e.target) && !e.target.closest('button[onclick="toggleUserDropdown()"]')) {
        popup.classList.add('hidden');
    }
});

function logoutNow() {
    localStorage.clear();
    window.location.href = "index.html";
}

document.addEventListener('DOMContentLoaded', initHubSidebar);