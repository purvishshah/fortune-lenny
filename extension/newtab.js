// ===============================
// Fortune Lenny - New Tab Logic
// ===============================

let quotes = [];

// ---- Utilities ----

function randomIndex(max) {
  return Math.floor(Math.random() * max);
}

// ---- Rendering ----

function renderQuote(index) {
  const quoteObj = quotes[index];
  const words = `"${quoteObj.quote}"`.split(" ");
  const quoteEl = document.getElementById("quoteText");

  quoteEl.innerHTML = words
    .map((word, i) =>
      `<span class="word" style="animation-delay:${(i * 0.12).toFixed(2)}s">${word}</span>`
    )
    .join(" ");

  const speakerEl = document.getElementById("speakerText");
  speakerEl.textContent = `– ${quoteObj.speaker}`;
  speakerEl.style.animationDelay = `${(words.length * 0.12 + 0.3).toFixed(2)}s`;
  speakerEl.classList.remove("revealed");
  void speakerEl.offsetWidth; // force reflow to restart animation
  speakerEl.classList.add("revealed");
}

// ---- Initialization ----

function initialize() {
  fetch("quotes.json")
    .then(res => res.json())
    .then(data => {
      quotes = data;
      renderQuote(randomIndex(quotes.length));
    })
    .catch(error => {
      console.error("Failed to load quotes:", error);
    });
}

// ---- Start ----

document.addEventListener("DOMContentLoaded", initialize);
