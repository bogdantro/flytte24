// add in static/js/home.js
document.addEventListener('DOMContentLoaded', () => {
  const zip = document.getElementById('zip');
  if (zip) zip.addEventListener('input', () => {
    zip.value = zip.value.replace(/[^\d ]/g, '').slice(0, 10);
  });
});
