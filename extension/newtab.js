// ===============================
// Fortune Lenny - New Tab Logic
// ===============================

let quotes = [];
let currentIndex = null;

// ---- Utilities ----

function getTodayKey() {
  const today = new Date();
  return today.toISOString().slice(0, 10);
}

function randomIndex(max) {
  return Math.floor(Math.random() * max);
}

function saveDailyIndex(index) {
  localStorage.setItem("fortune_lenny_index", index);
  localStorage.setItem("fortune_lenny_date", getTodayKey());
}

function getSavedDailyIndex() {
  const savedDate = localStorage.getItem("fortune_lenny_date");
  const savedIndex = localStorage.getItem("fortune_lenny_index");

  if (savedDate === getTodayKey() && savedIndex !== null) {
    return parseInt(savedIndex, 10);
  }

  return null;
}

// ---- Rendering ----

function renderQuote(index) {
  const quoteObj = quotes[index];

  document.getElementById("quoteText").textContent = `“${quoteObj.quote}”`;
  document.getElementById("speakerText").textContent = `– ${quoteObj.speaker}`;
  document.getElementById("youtubeLink").href = quoteObj.youtube_url;
}

// ---- Initialization ----

function initialize() {
  fetch("quotes.json")
    .then(res => res.json())
    .then(data => {
      quotes = data;

      const savedIndex = getSavedDailyIndex();

      if (savedIndex !== null) {
        currentIndex = savedIndex;
      } else {
        currentIndex = randomIndex(quotes.length);
        saveDailyIndex(currentIndex);
      }

      renderQuote(currentIndex);
    })
    .catch(error => {
      console.error("Failed to load quotes:", error);
    });
}

// ---- Event Listeners ----

document.addEventListener("DOMContentLoaded", () => {
  initialize();

  const nextBtn = document.getElementById("nextQuoteBtn");

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      currentIndex = randomIndex(quotes.length);
      renderQuote(currentIndex);
    });
  }
});

// ---- Start ----

initialize();