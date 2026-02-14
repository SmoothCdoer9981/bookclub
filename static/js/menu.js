// Menu handling
document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!menuToggle.contains(e.target) && !navMenu.contains(e.target)) {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });

        // Swipe to close (touch devices)
        let touchStartX = null;
        let touchStartY = null;

        navMenu.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
            }
        });

        navMenu.addEventListener('touchend', (e) => {
            if (touchStartX === null || touchStartY === null) return;
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            const dx = touchEndX - touchStartX;
            const dy = touchEndY - touchStartY;

            // Detect horizontal swipe (left or right)
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
                // Swipe left or right closes the menu
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
            touchStartX = null;
            touchStartY = null;
        });
    }
});
