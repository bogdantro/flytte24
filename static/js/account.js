// MENU
function Acntmenu(){
    const sidebar = document.getElementById('Acntsidebar');
    const hamburger = document.getElementById('Acnthamburger');
  
    const body = document.getElementsByTagName('body')[0];
  
    if (window.getComputedStyle(sidebar,null).getPropertyValue("opacity") == '0'){
      hamburger.classList.add('click')  
      sidebar.classList.add('active')
      body.style.overflowY = 'hidden';
    } else{
      hamburger.classList.remove('click')  
      sidebar.classList.remove('active')
    }  
  };
  
  