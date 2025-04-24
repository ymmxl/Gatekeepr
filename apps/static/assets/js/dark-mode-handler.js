const themeSwitch = document.getElementById("theme-switch");
const themeIndicator = document.getElementById("theme-indicator");
const page = document.body;
const logoLightElements = document.querySelectorAll('.logo-light');
const logoDarkElements = document.querySelectorAll('.logo-dark');

const themeStates = ["light", "dark"]
const indicators = ["fa-moon", "fa-sun"]
const pageClass = ["bg-gray-100", "dark-page"]

let currentTheme = localStorage.getItem("theme");

function setTheme(theme) {
    localStorage.setItem("theme", themeStates[theme])
}

function setIndicator(theme) {
    themeIndicator.classList.remove(indicators[0])
    themeIndicator.classList.remove(indicators[1])
    themeIndicator.classList.add(indicators[theme])
}

function setPage(theme) {
    page.classList.remove(pageClass[0])
    page.classList.remove(pageClass[1])
    page.classList.add(pageClass[theme])
}

function setLogo(theme) {
    if (logoLightElements.length > 0 && logoDarkElements.length > 0) {
        if (theme === 0) { // light theme
            logoLightElements.forEach(element => element.classList.remove('d-none'));
            logoDarkElements.forEach(element => element.classList.add('d-none'));
        } else { // dark theme
            logoLightElements.forEach(element => element.classList.add('d-none'));
            logoDarkElements.forEach(element => element.classList.remove('d-none'));
        }
    }
}

if (currentTheme === null) {
    localStorage.setItem("theme", themeStates[0])
    setIndicator(0)
    setPage(0)
    setLogo(0)
    themeSwitch.checked = true;
}
if (currentTheme === themeStates[0]) {
    setIndicator(0)
    setPage(0)
    setLogo(0)
    themeSwitch.checked = true;
}
if (currentTheme === themeStates[1]) {
    setIndicator(1)
    setPage(1)
    setLogo(1)
    themeSwitch.checked = false;
}


themeSwitch.addEventListener('change', function () {
    if (this.checked) {
        setTheme(0)
        setIndicator(0)
        setPage(0)
        setLogo(0)
    } else {
        setTheme(1)
        setIndicator(1)
        setPage(1)
        setLogo(1)
    }
});