// Progressive enhancements only: all store actions also work without JavaScript.
document.querySelectorAll('.filters select').forEach(select => {
  select.addEventListener('change', () => select.form.requestSubmit());
});
document.querySelectorAll('[data-checkout]').forEach(form => {
  form.addEventListener('submit', () => {
    const button = form.querySelector('[data-submit]');
    button.disabled = true;
    button.textContent = 'Placing your order...';
  });
});
window.addEventListener('pageshow', () => {
  document.querySelectorAll('[data-submit]').forEach(button => {
    button.disabled = false;
    button.textContent = 'Place mock order →';
  });
});
