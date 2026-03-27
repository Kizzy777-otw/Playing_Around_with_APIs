document.addEventListener("DOMContentLoaded", () => {
    const usdElem = document.getElementById("usd-value");
    fetch("/convert")
        .then(res => res.json())
        .then(data => {
            if (!data.error) {
                usdElem.textContent = `≈ $${data.usd}`;
            } else {
                usdElem.textContent = "Conversion unavailable";
            }
        });
});