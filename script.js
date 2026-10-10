/**
 * Library Management System (LMS) - Client-Side Application Script
 * Author: SHAHANAWAJ (Roll No: 2410302051)
 */

document.addEventListener("DOMContentLoaded", () => {
    initThemeManager();
    initMobileSidebar();
    initAutoDismissFlashes();
});

/* ==========================================================================
   1. Theme Management (Dark / Light Mode)
   ========================================================================== */
function initThemeManager() {
    const toggleBtn = document.getElementById("themeToggleBtn");
    const themeLabel = document.getElementById("themeLabel");
    if (!toggleBtn) return;

    // Check stored or document theme
    const htmlEl = document.documentElement;
    let currentTheme = htmlEl.getAttribute("data-theme") || "dark";

    updateThemeUI(currentTheme);

    toggleBtn.addEventListener("click", async () => {
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        currentTheme = newTheme;

        // Immediate visual update
        htmlEl.setAttribute("data-theme", newTheme);
        document.body.className = `theme-${newTheme}`;
        updateThemeUI(newTheme);

        // Persist on backend
        try {
            await fetch("/toggle-theme", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ theme: newTheme })
            });
        } catch (e) {
            console.error("Failed to sync theme with server:", e);
        }
    });

    function updateThemeUI(theme) {
        if (themeLabel) {
            themeLabel.textContent = theme === "dark" ? "Dark" : "Light";
        }
    }
}

/* ==========================================================================
   2. Mobile Sidebar Drawer
   ========================================================================== */
function initMobileSidebar() {
    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.getElementById("sidebarToggleBtn");
    const closeBtn = document.getElementById("sidebarCloseBtn");

    if (!sidebar || !toggleBtn) return;

    toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("open");
    });

    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            sidebar.classList.remove("open");
        });
    }

    // Close when clicking outside of sidebar on mobile
    document.addEventListener("click", (e) => {
        if (window.innerWidth <= 768 && sidebar.classList.contains("open")) {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove("open");
            }
        }
    });
}

/* ==========================================================================
   3. Auto-Dismiss Flash Messages
   ========================================================================== */
function initAutoDismissFlashes() {
    const alerts = document.querySelectorAll(".flash-alert");
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-8px)";
            setTimeout(() => alert.remove(), 400);
        }, 5500);
    });
}

/* ==========================================================================
   4. Modals (Generic Confirm & Return Book)
   ========================================================================== */
function closeModal() {
    const modal = document.getElementById("genericModal");
    if (modal) modal.style.display = "none";
}

function openReturnModal(txId, bookTitle, memberName, isOverdue, overdueDays, currentFine) {
    const modal = document.getElementById("returnModal");
    const form = document.getElementById("returnForm");
    const titleEl = document.getElementById("returnBookTitle");
    const memberEl = document.getElementById("returnMemberName");
    const dateInput = document.getElementById("modalReturnDate");
    const fineBox = document.getElementById("returnFineNotice");
    const fineText = document.getElementById("returnFineText");

    if (!modal) return;

    form.action = `/return/${txId}`;
    if (titleEl) titleEl.textContent = bookTitle;
    if (memberEl) memberEl.textContent = memberName;

    // Today's date YYYY-MM-DD
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    if (dateInput) dateInput.value = `${yyyy}-${mm}-${dd}`;

    // Overdue notice
    const hasOverdue = (isOverdue === true || isOverdue === "True" || isOverdue === "1" || parseInt(overdueDays) > 0);
    if (fineBox && fineText) {
        if (hasOverdue && parseFloat(currentFine) > 0) {
            fineBox.style.display = "flex";
            fineText.textContent = `Loan is overdue by ${overdueDays} day(s). Fine due upon return: ₹${parseFloat(currentFine).toFixed(2)}`;
        } else {
            fineBox.style.display = "none";
        }
    }

    modal.style.display = "flex";
}

function closeReturnModal() {
    const modal = document.getElementById("returnModal");
    if (modal) modal.style.display = "none";
}

// Close modals when clicking backdrop
window.addEventListener("click", (e) => {
    const genericModal = document.getElementById("genericModal");
    const returnModal = document.getElementById("returnModal");
    if (e.target === genericModal) closeModal();
    if (e.target === returnModal) closeReturnModal();
});

// Prevent accessing protected pages via browser Back button after logout
window.addEventListener("pageshow", (event) => {
    if (event.persisted || (window.performance && window.performance.navigation && window.performance.navigation.type === 2)) {
        window.location.reload();
    }
});

