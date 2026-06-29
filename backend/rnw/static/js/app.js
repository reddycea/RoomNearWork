document.addEventListener("DOMContentLoaded", () => {
  const flashMessages = document.querySelectorAll(".flash, .alert");

  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.classList.add("is-fading");
    }, 4500);
  });

  const menuToggle = document.querySelector("[data-menu-toggle]");
  const menu = document.querySelector("[data-menu]");

  if (menuToggle && menu) {
    menuToggle.addEventListener("click", () => {
      menu.classList.toggle("is-open");
    });
  }

  const confirmForms = document.querySelectorAll("[data-confirm]");

  confirmForms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.getAttribute("data-confirm") || "Are you sure?";

      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });
});
