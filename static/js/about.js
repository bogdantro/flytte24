document.addEventListener('DOMContentLoaded', function () {
    const textElement = document.getElementById('dynamic-textabt');
    const texts = ["Get to know us better", "Become member today!"];
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
  