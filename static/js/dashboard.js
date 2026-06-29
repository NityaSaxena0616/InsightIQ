/* =====================================================
   InsightIQ Premium SaaS UI Interactions
   ===================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Sidebar Toggle & Overlay Creation
    const topbarRight = document.querySelector(".topbar-right");
    const menuToggle = document.querySelector(".menu-toggle");
    
    // Add mobile toggle button in JS if not present in template
    if (!menuToggle && topbarRight) {
        const toggleBtn = document.createElement("button");
        toggleBtn.className = "menu-toggle";
        toggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        // Insert before profile avatar
        const profile = document.querySelector(".profile");
        if (profile) {
            topbarRight.insertBefore(toggleBtn, profile);
        } else {
            topbarRight.appendChild(toggleBtn);
        }
        
        // Add click listener
        toggleBtn.addEventListener("click", toggleSidebar);
    } else if (menuToggle) {
        menuToggle.addEventListener("click", toggleSidebar);
    }
    
    // Dynamically insert sidebar overlay
    let overlay = document.querySelector(".sidebar-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "sidebar-overlay";
        document.body.appendChild(overlay);
    }
    overlay.addEventListener("click", closeSidebar);

    function toggleSidebar() {
        document.body.classList.toggle("sidebar-active");
    }

    function closeSidebar() {
        document.body.classList.remove("sidebar-active");
    }

    // 2. Keyboard Shortcuts (Linear-style Cmd+K / Ctrl+K search focus)
    const searchInput = document.querySelector(".search-box input");
    const searchKbd = document.querySelector(".search-kbd");

    // Detect platform for keyboard shortcuts representation
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    if (searchKbd) {
        searchKbd.textContent = isMac ? "⌘K" : "Ctrl K";
    }

    document.addEventListener("keydown", (e) => {
        // Cmd+K or Ctrl+K
        if ((e.metaKey || e.ctrlKey) && e.key === "k") {
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
            }
        }
    });

    // 3. Page Fade-In Transition
    const fadeContainer = document.querySelector(".fade");
    if (fadeContainer) {
        fadeContainer.style.opacity = "0";
        // Let CSS animation handle it after render
        setTimeout(() => {
            fadeContainer.style.opacity = "1";
        }, 50);
    }
});
