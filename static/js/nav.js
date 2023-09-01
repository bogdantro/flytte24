
window.addEventListener("scroll", function(){
    const navbar = document.getElementById('mobileNav');
    navbar.classList.toggle("sticky", window.scrollY > 1)
  })


  window.addEventListener("scroll", function(){
    const navbar = document.getElementById('desNav');
    navbar.classList.toggle("sticky", window.scrollY > 1)
})




function search(){
  const search = document.getElementById('mobSidebarSearch');
  const hamburger = document.getElementById('hamburger');
  const navbar = document.getElementById('mobileNav');

  if (window.getComputedStyle(search,null).getPropertyValue("opacity") == '0'){
    search.classList.add('active');
    navbar.classList.add('search')
    hamburger.style.pointerEvents = 'none';
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
  }else{
    search.classList.remove('active');
    navbar.classList.remove('search')
    hamburger.style.pointerEvents = 'visible';
    document.body.style.overflow = "scroll";
    document.documentElement.style.overflow = "scroll";
  }
}  




/////////// MOBILE JAVASCRIPT
// MENU
function menu(){
  const sidebar = document.getElementById('sidebar');
  const navbar = document.getElementById('mobileNav');
  const hamburger = document.getElementById('hamburger');
  const search = document.getElementById('mobNavSearchIcon');

  const dropdown = document.getElementById('sidebarServDrop');

  const body = document.getElementsByTagName('body')[0];

  if (window.getComputedStyle(sidebar,null).getPropertyValue("opacity") == '0'){
    navbar.classList.add('menu')  
    hamburger.classList.add('click')  
    sidebar.classList.add('active')
    search.style.pointerEvents = 'none';
    body.style.overflowY = 'hidden';
    dropdown.classList.remove('active')
  } else{
    search.style.pointerEvents = 'visible';
    navbar.classList.remove('menu') 
    hamburger.classList.remove('click')  
    sidebar.classList.remove('active')
  }  
};

