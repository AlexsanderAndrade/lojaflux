document.addEventListener("DOMContentLoaded", () => {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  const localValue = now.toISOString().slice(0, 16);
  document.querySelectorAll(".datetime-now").forEach((input) => {
    if (!input.value) input.value = localValue;
  });

  const quantities = [...document.querySelectorAll(".sale-quantity")];
  const total = document.querySelector("#sale-total");
  const updateTotal = () => {
    const cents = quantities.reduce((sum, input) => {
      return sum + Number(input.dataset.price || 0) * Number(input.value || 0);
    }, 0);
    if (total) {
      total.textContent = new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
      }).format(cents / 100);
    }
  };
  quantities.forEach((input) => input.addEventListener("input", updateTotal));
  updateTotal();
});

