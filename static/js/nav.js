
window.addEventListener("scroll", function(){
    const navbar = document.getElementById('mobileNav');
    navbar.classList.toggle("sticky", window.scrollY > 1)
  })


  window.addEventListener("scroll", function(){
    const navbar = document.getElementById('desNav');
    navbar.classList.toggle("sticky", window.scrollY > 1)
})







function menu(){
  const sidebar = document.getElementById('sidebar');
  const navbar = document.getElementById('mobileNav');
  const hamburger = document.getElementById('lines');
  const menuText = document.getElementById('menuText');


  const body = document.getElementsByTagName('body')[0];

  if (window.getComputedStyle(sidebar,null).getPropertyValue("opacity") == '0'){
    navbar.classList.add('menu')  
    hamburger.classList.add('click')  
    sidebar.classList.add('active')
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";

    menuText.innerHTML = 'Lukk';

  } else{
    navbar.classList.remove('menu') 
    hamburger.classList.remove('click')  
    sidebar.classList.remove('active')

    menuText.innerHTML = 'Meny';

    document.body.style.overflow = "scroll";
    document.documentElement.style.overflow = "scroll";

  }  
}

