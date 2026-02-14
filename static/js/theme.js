// Theme handling
document.addEventListener('DOMContentLoaded', () => {
    console.log('Theme script loaded');

    const themeToggleButton = document.querySelector('.theme-toggle-btn');

    // Function to toggle theme
    const toggleTheme = () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateToggleButton(newTheme);
    };

    // Function to update the toggle button state
    const updateToggleButton = (theme) => {
        if (theme === 'dark') {
            themeToggleButton.setAttribute('data-theme', 'dark');
            themeToggleButton.querySelector('.sun-icon').style.display = 'none';
            themeToggleButton.querySelector('.moon-icon').style.display = 'block';
        } else {
            themeToggleButton.setAttribute('data-theme', 'light');
            themeToggleButton.querySelector('.sun-icon').style.display = 'block';
            themeToggleButton.querySelector('.moon-icon').style.display = 'none';
        }
    };

    // Initialize theme based on saved preference or default to light
    const initializeTheme = () => {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateToggleButton(savedTheme);
    };

    // Add event listener to the toggle button
    themeToggleButton.addEventListener('click', toggleTheme);

    // Initialize theme on page load
    initializeTheme();
});