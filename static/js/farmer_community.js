document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    const searchInput = document.getElementById("searchInput");
    const topicCards = document.querySelectorAll(".topic-card");
    const noResults = document.getElementById("noResults");

    if (!searchInput) return;

    searchInput.addEventListener("input", () => {
        const query = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        topicCards.forEach(card => {
            const text = card.textContent.toLowerCase();

            if (text.includes(query)) {
                card.style.display = "";
                visibleCount++;
            } else {
                card.style.display = "none";
            }
        });

        if (noResults) {
            noResults.classList.toggle("d-none", visibleCount > 0);
        }
    });
});

setTimeout(() => {
   document.querySelectorAll('.alert').forEach(a => a.remove());
}, 3000);