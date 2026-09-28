const $ = (id) => document.getElementById(id);

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    $(tab.dataset.panel).classList.add("active");
  });
});

function language() {
  return $("language").value;
}

function showStatus(message = "") {
  $("status").textContent = message;
}

function showResult(id, html) {
  const el = $(id);
  el.classList.remove("hidden");
  el.innerHTML = html;
}

function setBusy(id, busy) {
  const button = $(id);
  button.disabled = busy;
  if (busy) {
    button.dataset.original = button.textContent;
    button.textContent = "Working…";
  } else {
    button.textContent = button.dataset.original || button.textContent;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

async function apiJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed.");
  return data;
}

$("ask-btn").addEventListener("click", async () => {
  const question = $("question").value.trim();
  if (!question) return showStatus("Please enter a question.");
  setBusy("ask-btn", true); showStatus("Asking EduGenie…");
  try {
    const data = await apiJson("/api/ask", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({question, language:language()})
    });
    showResult("ask-result", `<strong>Answer</strong><p>${escapeHtml(data.answer).replace(/\n/g,"<br>")}</p>`);
    showStatus("");
  } catch (e) { showStatus(e.message); }
  finally { setBusy("ask-btn", false); }
});

$("quiz-btn").addEventListener("click", async () => {
  const topic = $("quiz-topic").value.trim();
  const file = $("quiz-file").files[0];
  if (!topic && !file) return showStatus("Enter a topic or upload a study file.");
  const form = new FormData();
  form.append("topic", topic); form.append("language", language());
  if (file) form.append("file", file);
  setBusy("quiz-btn", true); showStatus("Generating your quiz…");
  try {
    const data = await apiJson("/api/quiz", {method:"POST", body:form});
    const questions = data.quiz || [];
    window.__quiz = questions;
    showResult("quiz-result", renderQuiz(questions));
    showStatus("");
  } catch (e) { showStatus(e.message); }
  finally { setBusy("quiz-btn", false); }
});

function renderQuiz(questions) {
  if (!questions.length) return "<p>No quiz questions were returned.</p>";
  return `<form id="quiz-form">
    ${questions.map((q,i) => `
      <div class="quiz-question">
        <h4>${i+1}. ${escapeHtml(q.question)}</h4>
        ${Object.entries(q.options).map(([key,value]) => `
          <label class="option">
            <input type="radio" name="q${i}" value="${key}"> <strong>${key}</strong> ${escapeHtml(value)}
          </label>`).join("")}
        <div class="explanation hidden" id="exp-${i}">${escapeHtml(q.explanation)}</div>
      </div>`).join("")}
    <button type="submit" class="primary">Check Answers</button>
  </form>`;
}

document.addEventListener("submit", (event) => {
  if (event.target.id !== "quiz-form") return;
  event.preventDefault();
  const questions = [...document.querySelectorAll(".quiz-question")];
  let score = 0;
  questions.forEach((_,i) => {
    const answer = document.querySelector(`input[name="q${i}"]:checked`);
    const correct = window.__quiz?.[i]?.correct;
    if (answer && answer.value === correct) score++;
    $(`exp-${i}`).classList.remove("hidden");
  });
  showStatus(`Score: ${score}/${questions.length}`);
});

window.__quiz = [];
$("summary-btn").addEventListener("click", async () => {
  const content = $("summary-content").value.trim();
  const file = $("summary-file").files[0];
  if (!content && !file) return showStatus("Paste material or upload a file.");
  const form = new FormData();
  form.append("content", content); form.append("language", language());
  if (file) form.append("file", file);
  setBusy("summary-btn", true); showStatus("Summarizing…");
  try {
    const data = await apiJson("/api/summary", {method:"POST", body:form});
    showResult("summary-result", `<strong>Summary</strong><p>${escapeHtml(data.summary).replace(/\n/g,"<br>")}</p>`);
    showStatus("");
  } catch (e) { showStatus(e.message); }
  finally { setBusy("summary-btn", false); }
});

$("path-btn").addEventListener("click", async () => {
  const topic = $("path-topic").value.trim();
  const goal = $("path-goal").value.trim();
  if (!topic || !goal) return showStatus("Enter both a topic and a goal.");
  setBusy("path-btn", true); showStatus("Building your learning path…");
  try {
    const data = await apiJson("/api/learning-path", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        topic, goal, language:language(),
        current_level:$("path-level").value,
        hours_per_week:Number($("path-hours").value)
      })
    });
    showResult("path-result", renderPath(data));
    showStatus("");
  } catch (e) { showStatus(e.message); }
  finally { setBusy("path-btn", false); }
});

function renderPath(data) {
  return `<strong>${escapeHtml(data.topic)} — 6-week plan</strong>
  ${data.weeks.map(w => `
    <div class="path-week">
      <h4>Week ${w.week}: ${escapeHtml(w.title)}</h4>
      <strong>Objectives</strong><ul>${w.objectives.map(x=>`<li>${escapeHtml(x)}</li>`).join("")}</ul>
      <strong>Activities</strong><ul>${w.activities.map(x=>`<li>${escapeHtml(x)}</li>`).join("")}</ul>
      <strong>Checkpoint:</strong> ${escapeHtml(w.checkpoint)}
    </div>`).join("")}`;
}
