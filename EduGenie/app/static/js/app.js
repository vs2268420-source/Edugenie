const $ = (id) => document.getElementById(id);

function initializeApp() {
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      panels.forEach((panel) => {
        const isActive = panel.id === tab.dataset.panel;
        panel.classList.toggle("active", isActive);
      });
    });
  });

  const askButton = $("ask-btn");
  if (askButton) {
    askButton.addEventListener("click", async () => {
      const questionInput = $("question");
      const question = questionInput ? questionInput.value.trim() : "";
      if (!question) return showStatus("Please enter a question.");
      setBusy("ask-btn", true);
      showStatus("Asking EduGenie…");
      try {
        const data = await apiJson("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, language: language() }),
        });
        showResult("ask-result", `<strong>Answer</strong><p>${escapeHtml(data.answer || "").replace(/\n/g, "<br>")}</p>`);
        showStatus("");
      } catch (error) {
        showStatus(error.message || "Request failed.");
      } finally {
        setBusy("ask-btn", false);
      }
    });
  }

  const quizButton = $("quiz-btn");
  if (quizButton) {
    quizButton.addEventListener("click", async () => {
      const topicInput = $("quiz-topic");
      const fileInput = $("quiz-file");
      const topic = topicInput ? topicInput.value.trim() : "";
      const file = fileInput ? fileInput.files[0] : null;
      if (!topic && !file) return showStatus("Enter a topic or upload a study file.");

      const form = new FormData();
      form.append("topic", topic);
      form.append("language", language());
      if (file) form.append("file", file);

      setBusy("quiz-btn", true);
      showStatus("Generating your quiz…");
      try {
        const data = await apiJson("/api/quiz", { method: "POST", body: form });
        const questions = Array.isArray(data.quiz) ? data.quiz : [];
        window.__quiz = questions;
        showResult("quiz-result", renderQuiz(questions));
        showStatus("");
      } catch (error) {
        showStatus(error.message || "Quiz generation failed.");
      } finally {
        setBusy("quiz-btn", false);
      }
    });
  }

  const summaryButton = $("summary-btn");
  if (summaryButton) {
    summaryButton.addEventListener("click", async () => {
      const contentInput = $("summary-content");
      const fileInput = $("summary-file");
      const content = contentInput ? contentInput.value.trim() : "";
      const file = fileInput ? fileInput.files[0] : null;
      if (!content && !file) return showStatus("Paste material or upload a file.");

      const form = new FormData();
      form.append("content", content);
      form.append("language", language());
      if (file) form.append("file", file);

      setBusy("summary-btn", true);
      showStatus("Summarizing…");
      try {
        const data = await apiJson("/api/summary", { method: "POST", body: form });
        showResult("summary-result", `<strong>Summary</strong><p>${escapeHtml(data.summary || "").replace(/\n/g, "<br>")}</p>`);
        showStatus("");
      } catch (error) {
        showStatus(error.message || "Summary failed.");
      } finally {
        setBusy("summary-btn", false);
      }
    });
  }

  const pathButton = $("path-btn");
  if (pathButton) {
    pathButton.addEventListener("click", async () => {
      const topicInput = $("path-topic");
      const goalInput = $("path-goal");
      const topic = topicInput ? topicInput.value.trim() : "";
      const goal = goalInput ? goalInput.value.trim() : "";
      if (!topic || !goal) return showStatus("Enter both a topic and a goal.");

      setBusy("path-btn", true);
      showStatus("Building your learning path…");
      try {
        const data = await apiJson("/api/learning-path", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            topic,
            goal,
            language: language(),
            current_level: $("path-level") ? $("path-level").value : "Beginner",
            hours_per_week: Number($("path-hours") ? $("path-hours").value : 5),
          }),
        });
        showResult("path-result", renderPath(data));
        showStatus("");
      } catch (error) {
        showStatus(error.message || "Learning path generation failed.");
      } finally {
        setBusy("path-btn", false);
      }
    });
  }

  document.addEventListener("submit", (event) => {
    if (event.target && event.target.id !== "quiz-form") return;
    event.preventDefault();

    const questions = [...document.querySelectorAll(".quiz-question")];
    const quizData = Array.isArray(window.__quiz) ? window.__quiz : [];
    if (!questions.length) {
      showStatus("No quiz questions are available to grade.");
      return;
    }

    let score = 0;
    questions.forEach((_, index) => {
      const answer = document.querySelector(`input[name="q${index}"]:checked`);
      const correct = quizData[index]?.correct;
      if (answer && answer.value === correct) score++;
      const explanation = $("exp-" + index);
      if (explanation) explanation.classList.remove("hidden");
    });

    showStatus(`Score: ${score}/${questions.length}`);
  });
}

function language() {
  const el = $("language");
  return el ? el.value : "English";
}

function showStatus(message = "") {
  const el = $("status");
  if (el) el.textContent = message;
}

function showResult(id, html) {
  const el = $(id);
  if (!el) return;
  el.classList.remove("hidden");
  el.innerHTML = html;
}

function setBusy(id, busy) {
  const button = $(id);
  if (!button) return;
  button.disabled = busy;
  if (busy) {
    button.dataset.original = button.textContent;
    button.textContent = "Working…";
  } else {
    button.textContent = button.dataset.original || button.textContent;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[character]));
}

async function apiJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed.");
  return data;
}

function renderQuiz(questions) {
  const safeQuestions = Array.isArray(questions) ? questions : [];
  if (!safeQuestions.length) return "<p>No quiz questions were returned.</p>";

  return `<form id="quiz-form">
    ${safeQuestions.map((question, index) => {
      const options = question && typeof question === "object" ? (question.options || {}) : {};
      const explanation = question && typeof question === "object" ? (question.explanation || "") : "";
      const choices = Object.entries(options)
        .map(([key, value]) => `
          <label class="option">
            <input type="radio" name="q${index}" value="${key}"> <strong>${key}</strong> ${escapeHtml(value || "")}
          </label>
        `)
        .join("") || "<p>No options available.</p>";

      return `
        <div class="quiz-question">
          <h4>${index + 1}. ${escapeHtml(question?.question || "Question unavailable")}</h4>
          ${choices}
          <div class="explanation hidden" id="exp-${index}">${escapeHtml(explanation)}</div>
        </div>
      `;
    }).join("")}
    <button type="submit" class="primary">Check Answers</button>
  </form>`;
}

function renderPath(data) {
  const weeks = Array.isArray(data?.weeks) ? data.weeks : [];
  if (!weeks.length) return "<p>No learning path data was returned.</p>";

  return `<strong>${escapeHtml(data.topic || "Learning path")} — 6-week plan</strong>
    ${weeks.map((week) => `
      <div class="path-week">
        <h4>Week ${week.week || ""}: ${escapeHtml(week.title || "Week plan")}</h4>
        <strong>Objectives</strong>
        <ul>${(week.objectives || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>None provided.</li>"}</ul>
        <strong>Activities</strong>
        <ul>${(week.activities || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>None provided.</li>"}</ul>
        <strong>Checkpoint:</strong> ${escapeHtml(week.checkpoint || "Review progress")}
      </div>
    `).join("")}`;
}

window.__quiz = [];
document.addEventListener("DOMContentLoaded", initializeApp);
