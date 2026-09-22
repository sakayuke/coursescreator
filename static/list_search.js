document.querySelectorAll("[data-search-toggle]").forEach((toggle) => {
    const form = document.getElementById(
        toggle.getAttribute("aria-controls")
    );
    const input = form.querySelector("input[type='search']");

    toggle.addEventListener("click", () => {
        const isOpen = form.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(isOpen));

        if (isOpen) {
            input.focus();
        }
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            form.classList.remove("is-open");
            toggle.setAttribute("aria-expanded", "false");
            toggle.focus();
        }
    });
});
