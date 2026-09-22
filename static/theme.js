
(function () {

    var STORAGE_KEY = "theme";

    var root = document.documentElement;
    var button = document.querySelector(".theme-toggle");
    var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");


    function currentTheme() {
        return root.getAttribute("data-theme")
            || localStorage.getItem(STORAGE_KEY)
            || (darkQuery.matches ? "dark" : "light");
    }


    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);

        if (button) {
            button.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
        }
    }


    applyTheme(currentTheme());


    if (button) {
        button.addEventListener("click", function () {
            var next = currentTheme() === "dark" ? "light" : "dark";

            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
        });
    }


    // Если пользователь ни разу не нажимал кнопку — следуем за системной темой.
    darkQuery.addEventListener("change", function (event) {
        if (!localStorage.getItem(STORAGE_KEY)) {
            applyTheme(event.matches ? "dark" : "light");
        }
    });

})();
