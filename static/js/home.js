// JavaScript for the page transition with white overlay
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.querySelector('.page-overlay');

    // Remove the overlay when the page has fully loaded
    overlay.style.opacity = 0;
    overlay.style.pointerEvents = 'none';

    // Listen for link clicks to initiate the transition
    const links = document.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();

            // Fade in the overlay
            overlay.style.opacity = 1;
            overlay.style.pointerEvents = 'auto';

            // Delay the actual navigation for a smooth effect
            setTimeout(() => {
                window.location.href = link.href;
            }, 500); // You can adjust the delay time to match the CSS transition duration
        });
    });
});
