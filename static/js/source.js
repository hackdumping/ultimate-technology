 // Mode sombre
 /*    themeToggle.addEventListener('click',()=>{
      document.body.classList.toggle('dark');
      themeToggle.textContent=document.body.classList.contains('dark')?"☀️":"🌙";
    });
  */

// Fonctions pour gérer le thème
function setTheme(theme) {
  //  document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    themeToggle.textContent = theme === 'dark' ? "☀️":"🌙";
    if(localStorage.getItem('theme') == 'dark'){
        document.body.classList.add('dark');
    }else{
        document.body.classList.remove('dark');
    }
}

function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    // Événement sur le toggle
    themeToggle.addEventListener('click', toggleTheme);
});

// Pour s'assurer que le thème est appliqué immédiatement
/*(function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
})();
*/



