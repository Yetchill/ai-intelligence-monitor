document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || !form.matches("[data-update-form]")) return;
  const button = form.querySelector("button[type='submit']");
  if (!(button instanceof HTMLButtonElement)) return;
  button.disabled = true;
  button.textContent = button.dataset.processingText || "处理中…";
  button.setAttribute("aria-busy", "true");
});
