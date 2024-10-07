window.onload = function() {
    document.getElementById('coverText').classList.add('active');
    document.getElementById('borderForImage').classList.add('active');
    document.getElementById('imageForBorder').classList.add('active');
};


document.addEventListener('DOMContentLoaded', function () {
  const textElement = document.getElementById('dynamic-text');
  const texts = ["Welcome to Villa Zen Garden", "Join us"];
  let currentIndex = 0; 
  let charIndex = 0; 
  let isTyping = true; // Keep track of whether we are typing or untyping
  let typingSpeed = 100;
  let untypingSpeed = 100;
  let holdTime = 2000; // Time to hold the text before untyping starts

  function typeEffect() {
    const currentText = texts[currentIndex];

    if (isTyping) {
      // Typing logic
      if (charIndex < currentText.length) {
        // Append the next character and increment charIndex
        textElement.textContent = currentText.substring(0, charIndex + 1);
        charIndex++;
      } else {
        // Once typing is done, wait and then start untyping
        isTyping = false;
        setTimeout(typeEffect, holdTime); // Hold the text for some time
        return; // Stop typing to let holdTime delay work
      }
    } else {
      // Untyping logic
      if (charIndex > 0) {
        // Remove characters one by one
        textElement.textContent = currentText.substring(0, charIndex - 1);
        charIndex--;
      } else {
        // Once untyping is done, switch to the next text
        isTyping = true;
        currentIndex = (currentIndex + 1) % texts.length; // Move to the next text
      }
    }
    
    // Recursively call the typeEffect with correct speed
    const speed = isTyping ? typingSpeed : untypingSpeed;
    setTimeout(typeEffect, speed);
  }

  // Start the typing effect
  typeEffect();
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

