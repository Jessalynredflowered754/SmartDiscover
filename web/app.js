const form = document.getElementById("recommendForm");
const intentInput = document.getElementById("intentInput");
const targetCountInput = document.getElementById("targetCountInput");
const submitBtn = document.getElementById("submitBtn");
const healthBtn = document.getElementById("healthBtn");
const llmBadge = document.getElementById("llmBadge");
const spotifyBadge = document.getElementById("spotifyBadge");
const quickPrompts = document.getElementById("quickPrompts");
const statusText = document.getElementById("statusText");
const recommendationList = document.getElementById("recommendationList");
const resultLead = document.getElementById("resultLead");
const summaryMood = document.getElementById("summaryMood");
const summaryActivity = document.getElementById("summaryActivity");
const summaryCount = document.getElementById("summaryCount");
const summaryMode = document.getElementById("summaryMode");
const agentFlow = document.getElementById("agentFlow");
const agentStageText = document.getElementById("agentStageText");
const agentMetrics = document.getElementById("agentMetrics");
const pillProfiler = document.getElementById("pillProfiler");
const pillSearch = document.getElementById("pillSearch");
const pillRanker = document.getElementById("pillRanker");
const pillPresenter = document.getElementById("pillPresenter");

let agentStageTimer = null;
let replayToken = 0;
const stagePills = [pillProfiler, pillSearch, pillRanker, pillPresenter];

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#ff8f8f" : "#a2cad4";
}

function setLlmBadge(text, tone = "neutral") {
  llmBadge.classList.remove("neutral", "ok", "warn", "error");
  llmBadge.classList.add(tone);
  llmBadge.textContent = text;
}

function setSpotifyBadge(text, tone = "neutral") {
  spotifyBadge.classList.remove("neutral", "ok", "warn", "error");
  spotifyBadge.classList.add(tone);
  spotifyBadge.textContent = text;
}

function setAgentStage(stage, text) {
  agentFlow.dataset.stage = String(stage);
  agentStageText.textContent = text;
  const visualByStage = {
    0: "idle",
    1: "profiler",
    2: "search",
    3: "ranker",
    4: "presenter",
  };
  setRuntimeVisualState(visualByStage[stage] || "idle");
  stagePills.forEach((pill, index) => {
    const n = index + 1;
    pill.classList.toggle("active", n === stage);
    pill.classList.toggle("done", stage > 0 && n < stage);
  });
}

function setAgentMetrics(text) {
  agentMetrics.textContent = text;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function setRuntimeVisualState(state) {
  const pipeline = document.querySelector('.agent-pipeline');
  if (pipeline) {
    pipeline.className = `agent-pipeline state-${state}`;
  }
}

async function replayStagesFromMetrics(stageMs) {
  const token = ++replayToken;
  const sequence = [
    [1, "Profiler Agent • Memahami mood dan aktivitas", Number(stageMs?.profiler || 0)],
    [2, "Spotify Search Agent • Menelusuri kandidat lagu", Number(stageMs?.search || 0)],
    [3, "Filter & Ranker Agent • Menilai relevansi", Number(stageMs?.ranker || 0)],
    [4, "Presenter Agent • Menyusun hasil terbaik", Number(stageMs?.presenter || 0)],
  ];

  agentFlow.classList.add("is-working");
  agentFlow.classList.remove("is-done");

  for (const [stage, label, rawMs] of sequence) {
    if (token !== replayToken) {
      return;
    }
    setAgentStage(stage, label);
    const waitMs = Math.min(1600, Math.max(320, rawMs));
    await delay(waitMs);
  }

  if (token !== replayToken) {
    return;
  }
  agentFlow.classList.remove("is-working");
  agentFlow.classList.add("is-done");
  setAgentStage(4, "Selesai • Playlist siap diputar");
  setRuntimeVisualState("done");
}

function stopAgentAnimation(isSuccess, stageMs = null) {
  replayToken += 1;
  if (agentStageTimer) {
    clearInterval(agentStageTimer);
    agentStageTimer = null;
  }

  agentFlow.classList.remove("is-working");
  agentFlow.classList.toggle("is-done", Boolean(isSuccess));

  if (isSuccess) {
    if (stageMs) {
      setAgentMetrics("Pipeline selesai. Semua agent telah mengeksekusi tahapan dengan sukses.");
      replayStagesFromMetrics(stageMs);
    } else {
      setAgentStage(4, "Selesai • Playlist siap diputar");
      setRuntimeVisualState("done");
      setAgentMetrics("Pipeline selesai. Playlist siap diputar.");
    }
  } else {
    setAgentStage(0, "Terhenti • Coba lagi");
    setRuntimeVisualState("error");
    setAgentMetrics("Milestone backend tidak tersedia karena request gagal.");
  }
}

function startAgentAnimation() {
  if (agentStageTimer) {
    clearInterval(agentStageTimer);
  }

  const stages = [
    [1, "Profiler Agent • Memahami mood dan aktivitas"],
    [2, "Spotify Search Agent • Menelusuri kandidat lagu"],
    [3, "Filter & Ranker Agent • Menilai relevansi"],
    [4, "Presenter Agent • Menyusun hasil terbaik"],
  ];

  let idx = 0;
  agentFlow.classList.remove("is-done");
  agentFlow.classList.add("is-working");
  setAgentMetrics("Merekam progres backend...");
  setAgentStage(stages[idx][0], stages[idx][1]);

  agentStageTimer = setInterval(() => {
    idx = (idx + 1) % stages.length;
    setAgentStage(stages[idx][0], stages[idx][1]);
  }, 900);
}

function renderSummary(data) {
  const profile = data.intent_profile || {};
  const quality = data.quality_notes || {};

  summaryMood.textContent = profile.mood || "-";
  summaryActivity.textContent = profile.activity || "-";
  summaryCount.textContent = String(data.summary?.returned_count ?? 0);

  const profilerMode = quality.llm_profiler_used ? "LLM" : "Heuristic";
  const rankerMode = quality.llm_ranker_used ? "LLM" : "Heuristic";
  summaryMode.textContent = `${profilerMode}/${rankerMode}`;
}

function renderRecommendations(data) {
  recommendationList.innerHTML = "";
  const list = data.recommendations || [];

  if (!list.length) {
    recommendationList.innerHTML = "<p class=\"empty-state\">Belum ada rekomendasi. Coba ubah deskripsi mood kamu.</p>";
    resultLead.textContent = "Belum ada hasil yang cocok. Ubah deskripsi mood atau aktivitas untuk hasil yang lebih pas.";
    return;
  }

  resultLead.textContent = `${list.length} lagu dipilih untuk kamu. Klik alasan jika ingin melihat detail lebih banyak.`;

  list.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "track-card enter";
    card.style.setProperty("--stagger-index", String(index));

    const top = document.createElement("div");
    top.className = "track-top";

    const rank = document.createElement("p");
    rank.className = "track-rank";
    rank.textContent = `#${item.rank}`;

    const score = document.createElement("p");
    score.className = "track-score";
    score.textContent = `match ${Math.round(Number(item.score || 0) * 100)}%`;

    top.appendChild(rank);
    top.appendChild(score);

    const title = document.createElement("p");
    title.className = "track-title";
    title.textContent = item.title;

    const meta = document.createElement("p");
    meta.className = "track-meta";
    meta.textContent = `${item.artist} | score: ${Number(item.score).toFixed(4)}`;

    const why = document.createElement("p");
    why.className = "track-why";
    why.textContent = item.why || "Alasan belum tersedia.";

    const isLongReason = why.textContent.length > 110;
    if (isLongReason) {
      why.classList.add("collapsed");
    }

    const actions = document.createElement("div");
    actions.className = "track-actions";

    if (isLongReason) {
      const toggleWhy = document.createElement("button");
      toggleWhy.className = "text-btn";
      toggleWhy.type = "button";
      toggleWhy.textContent = "Lihat alasan";
      toggleWhy.addEventListener("click", () => {
        const collapsed = why.classList.toggle("collapsed");
        toggleWhy.textContent = collapsed ? "Lihat alasan" : "Sembunyikan";
      });
      actions.appendChild(toggleWhy);
    }

    card.appendChild(top);
    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(why);

    if (item.spotify_url) {
      const link = document.createElement("a");
      link.className = "track-link";
      link.href = item.spotify_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Buka di Spotify";
      actions.appendChild(link);
    }

    if (actions.childElementCount > 0) {
      card.appendChild(actions);
    }

    recommendationList.appendChild(card);
  });
}

function renderLoadingSkeleton(targetCount) {
  const count = Math.max(4, Math.min(Number(targetCount) || 6, 8));
  recommendationList.innerHTML = "";
  resultLead.textContent = "Sedang menyiapkan daftar lagu paling cocok...";

  for (let i = 0; i < count; i += 1) {
    const card = document.createElement("article");
    card.className = "skeleton-card";

    const line1 = document.createElement("div");
    line1.className = "skeleton-line short";

    const line2 = document.createElement("div");
    line2.className = "skeleton-line";

    const line3 = document.createElement("div");
    line3.className = "skeleton-line medium";

    card.appendChild(line1);
    card.appendChild(line2);
    card.appendChild(line3);
    recommendationList.appendChild(card);
  }
}

async function requestRecommendations(event) {
  event.preventDefault();
  const text = intentInput.value.trim();
  const targetCount = Number(targetCountInput.value || 15);

  if (!text) {
    setStatus("Intent wajib diisi.", true);
    return;
  }

  submitBtn.disabled = true;
  setStatus("Mencari rekomendasi terbaik untuk kamu...");
  startAgentAnimation();
  renderLoadingSkeleton(targetCount);

  try {
    const response = await fetch("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_count: targetCount }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Request failed (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    renderSummary(data);
    renderRecommendations(data);

    const quality = data.quality_notes || {};
    const profilerMode = quality.llm_profiler_used ? "LLM" : "heuristic";
    const rankerMode = quality.llm_ranker_used ? "LLM" : "heuristic";

    setStatus(
      `${data.summary.returned_count} lagu ditemukan. Profiler=${profilerMode}, Ranker=${rankerMode}.`
    );
    stopAgentAnimation(true, data.quality_notes?.stage_ms || null);
  } catch (error) {
    setStatus(error.message || "Terjadi error saat memanggil API.", true);
    recommendationList.innerHTML = "<p class=\"empty-state\">Gagal memuat rekomendasi. Coba lagi sebentar.</p>";
    resultLead.textContent = "Terjadi kendala saat mengambil rekomendasi.";
    stopAgentAnimation(false);
  } finally {
    submitBtn.disabled = false;
  }
}

async function checkLlmHealth(showStatusMessage = false) {
  setLlmBadge("LLM: checking...", "neutral");

  try {
    const response = await fetch("/llm/health");
    if (!response.ok) {
      throw new Error(`LLM health failed (${response.status})`);
    }
    const data = await response.json();
    const model = data.model || "unknown-model";

    if (data.ok) {
      setLlmBadge(`LLM: online (${model})`, "ok");
      if (showStatusMessage) {
        setStatus(`LLM ready on model ${model}.`);
      }
      return;
    }

    const isDisabled = data.status === "disabled";
    setLlmBadge(
      isDisabled ? "LLM: disabled (fallback active)" : "LLM: degraded",
      isDisabled ? "warn" : "error"
    );

    if (showStatusMessage) {
      setStatus(`LLM status: ${data.status}. ${data.details || ""}`.trim(), !isDisabled);
    }
  } catch (error) {
    setLlmBadge("LLM: unreachable", "error");
    if (showStatusMessage) {
      setStatus(error.message || "Gagal cek LLM health.", true);
    }
  }
}

async function checkSpotifyHealth() {
  healthBtn.disabled = true;
  setStatus("Checking Spotify health...");

  try {
    const response = await fetch("/spotify/health");
    if (!response.ok) {
      throw new Error(`Spotify health failed (${response.status})`);
    }
    const data = await response.json();
    const detail = data.details ? ` ${data.details}` : "";
    if (data.ok) {
      setSpotifyBadge("Spotify: online", "ok");
    } else if (data.status === "mock-mode") {
      setSpotifyBadge("Spotify: mock mode", "warn");
    } else {
      setSpotifyBadge("Spotify: degraded", "error");
    }
    setStatus(`Spotify: ${data.status}.${detail}`);
  } catch (error) {
    setSpotifyBadge("Spotify: unreachable", "error");
    setStatus(error.message || "Gagal cek Spotify health.", true);
  } finally {
    healthBtn.disabled = false;
  }
}

function bindQuickPrompts() {
  quickPrompts.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) {
      return;
    }
    const intent = target.dataset.intent;
    if (!intent) {
      return;
    }
    intentInput.value = intent;
    intentInput.focus();
    setStatus("Contoh intent terisi. Kamu bisa langsung cari rekomendasi.");
  });
}

form.addEventListener("submit", requestRecommendations);
healthBtn.addEventListener("click", checkSpotifyHealth);
bindQuickPrompts();
checkLlmHealth();
checkSpotifyHealth();
setAgentStage(0, "Idle • Menunggu perintah");
setAgentMetrics("Milestone backend akan tampil setelah request selesai.");
