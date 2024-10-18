window.onload = function() {
  setTimeout(() => {
    document.getElementById('coverText').classList.add('active');
  }, 500);
    document.getElementById('borderForImage').classList.add('active');
    document.getElementById('imageForBorder').classList.add('active');
};




document.addEventListener('DOMContentLoaded', function () {
  const textElement = document.getElementById('dynamic-text');
  const overlay = document.getElementById('overlay');

  // Trigger the overlay animation
  setTimeout(() => {
    overlay.classList.add('active');
  }, 1000);

  // The text to be typed
  const texts = ['Find your ways'];
  let currentIndex = 0; // Index of the current text in the array
  let charIndex = 0; // Start typing from the first character
  let typingSpeed = 100; // Speed of typing in milliseconds

  function typeEffect() {
    const currentText = texts[currentIndex];

    // Typing logic
    if (charIndex < currentText.length) {
      // Append the next character and increment charIndex
      textElement.textContent = currentText.substring(0, charIndex + 1);
      charIndex++;
      
      // Continue typing
      setTimeout(typeEffect, typingSpeed);
    }
  }

  setTimeout(() => {
    // Start typing immediately on page load
    typeEffect();
  }, 1700);
});





document.addEventListener("scroll", function() {
  const scrollIndicator = document.querySelector(".scroll-indicator");
  const txt = document.getElementById("coverText");
  const img = document.getElementById("imageForBorder");
  const border = document.getElementById("borderForImage");
  
  // If the page is scrolled down more than 50px, add the active class
  if (window.scrollY > 50) {
    scrollIndicator.classList.add("active");
    // txt.classList.add("scroll");
    // img.classList.add("scroll");
    // border.classList.add("scroll");
  } else {
    scrollIndicator.classList.remove("active");
    // txt.classList.remove("scroll");
    // img.classList.remove("scroll");
    // border.classList.remove("scroll");
  }
});