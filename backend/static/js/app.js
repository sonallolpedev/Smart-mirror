const clockEl = document.getElementById("clock");
const dateEl = document.getElementById("date");
const timezoneEl = document.getElementById("timezone");
const tempEl = document.getElementById("temp");
const cityEl = document.getElementById("city");
const conditionEl = document.getElementById("condition");
const healthEl = document.getElementById("health");
const updatedEl = document.getElementById("updated");
const motionStateEl = document.getElementById("motionState");
const emotionStateEl = document.getElementById("emotionState");
const scheduleDayEl = document.getElementById("scheduleDay");
const scheduleListEl = document.getElementById("scheduleList");
const scheduleDaySelectEl = document.getElementById("scheduleDaySelect");
const scheduleEditorEl = document.getElementById("scheduleEditor");
const saveScheduleBtnEl = document.getElementById("saveScheduleBtn");
const scheduleSaveStatusEl = document.getElementById("scheduleSaveStatus");
const newsSourceEl = document.getElementById("newsSource");
const newsListEl = document.getElementById("newsList");
const cameraFeedEl = document.getElementById("cameraFeed");
const cameraStatusEl = document.getElementById("cameraStatus");

let activeStream;
let motionTimer;
let previousMotionSample;
let emotionTimer;
let emotionModelsReady = false;
let handsDetector;
let gestureTimer;
let lastGestureToggleAt = 0;
let lastFaceDetectedAt = Date.now();
let autoSleepTimer;
let mirrorPowerState = "on";

const AUTO_OFF_MS = 30000;
const NEWS_REFRESH_MS = 24 * 60 * 60 * 1000;

const WEEK_DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

const scheduleCache = {};

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function refreshTime() {
  try {
    const data = await fetchJson("/api/time");
    clockEl.textContent = data.time;
    dateEl.textContent = data.date;
    if (timezoneEl) {
      timezoneEl.textContent = `Timezone: ${data.timezone || "Asia/Kolkata"}`;
    }
  } catch {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("en-GB", { hour12: false });
    dateEl.textContent = now.toDateString();
    if (timezoneEl) {
      timezoneEl.textContent = "Timezone: Asia/Kolkata";
    }
  }
}

async function refreshWeather() {
  try {
    const data = await fetchJson("/api/weather");
    tempEl.textContent = data.temp_c;
    conditionEl.textContent = data.condition;
    cityEl.textContent = `${data.city} (${data.source})`;
  } catch {
    conditionEl.textContent = "Unavailable";
  }
}

async function refreshStatus() {
  try {
    const data = await fetchJson("/api/status");
    healthEl.textContent = data.ok ? "Online" : "Offline";
    updatedEl.textContent = `Updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
  } catch {
    healthEl.textContent = "Offline";
    updatedEl.textContent = "Updated: --";
  }
}

async function refreshSchedule() {
  if (!scheduleListEl || !scheduleDayEl) {
    return;
  }

  try {
    const data = await fetchJson("/api/schedule");
    scheduleDayEl.textContent = data.day;
    const items = Array.isArray(data.items) ? data.items : [];
    scheduleListEl.innerHTML = "";

    if (!items.length) {
      const li = document.createElement("li");
      li.textContent = "No tasks planned for today.";
      scheduleListEl.appendChild(li);
      return;
    }

    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      scheduleListEl.appendChild(li);
    });
  } catch {
    scheduleDayEl.textContent = "Unavailable";
    scheduleListEl.innerHTML = "<li>Could not load schedule.</li>";
  }
}

async function refreshScheduleEditor() {
  if (!scheduleDaySelectEl || !scheduleEditorEl) {
    return;
  }

  try {
    const data = await fetchJson("/api/schedule/all");
    const schedule = data.schedule || {};
    WEEK_DAYS.forEach((day) => {
      scheduleCache[day] = Array.isArray(schedule[day]) ? schedule[day] : [];
    });

    if (!scheduleDaySelectEl.options.length) {
      WEEK_DAYS.forEach((day) => {
        const option = document.createElement("option");
        option.value = day;
        option.textContent = day;
        scheduleDaySelectEl.appendChild(option);
      });
    }

    const selectedDay = scheduleDaySelectEl.value || WEEK_DAYS[0];
    scheduleDaySelectEl.value = selectedDay;
    scheduleEditorEl.value = (scheduleCache[selectedDay] || []).join("\n");
    if (scheduleSaveStatusEl) {
      scheduleSaveStatusEl.textContent = "Loaded schedule from server.";
    }
  } catch {
    if (scheduleSaveStatusEl) {
      scheduleSaveStatusEl.textContent = "Could not load schedule editor data.";
    }
  }
}

async function saveScheduleForSelectedDay() {
  if (!scheduleDaySelectEl || !scheduleEditorEl || !scheduleSaveStatusEl) {
    return;
  }

  const day = scheduleDaySelectEl.value;
  const items = scheduleEditorEl.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  scheduleSaveStatusEl.textContent = "Saving...";

  try {
    const response = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ day, items }),
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Failed to save schedule");
    }

    scheduleCache[day] = data.items;
    scheduleSaveStatusEl.textContent = `Saved ${day} schedule.`;
    await refreshSchedule();
  } catch (error) {
    scheduleSaveStatusEl.textContent = `Save failed: ${error.message}`;
  }
}

async function refreshNews() {
  if (!newsListEl || !newsSourceEl) {
    return;
  }

  try {
    const data = await fetchJson("/api/news?topic=technology");
    const headlines = Array.isArray(data.headlines) ? data.headlines : [];
    const cacheLabel = data.cached ? "cached" : "fresh";
    newsSourceEl.textContent = `India technology | Source: ${data.source || "unknown"} (${cacheLabel})`;
    newsListEl.innerHTML = "";

    if (!headlines.length) {
      const li = document.createElement("li");
      li.textContent = "No headlines right now.";
      newsListEl.appendChild(li);
      return;
    }

    headlines.slice(0, 4).forEach((headline) => {
      const li = document.createElement("li");
      li.textContent = headline;
      newsListEl.appendChild(li);
    });
  } catch {
    newsSourceEl.textContent = "Source: unavailable";
    newsListEl.innerHTML = "<li>Could not load news.</li>";
  }
}

async function refreshAll() {
  await Promise.all([
    refreshTime(),
    refreshWeather(),
    refreshStatus(),
    refreshSchedule(),
    refreshNews(),
  ]);
}

function setCameraStatus(message) {
  if (cameraStatusEl) {
    cameraStatusEl.textContent = message;
  }
}

function setMirrorPowerState(nextState, reason) {
  mirrorPowerState = nextState;
  const isOn = nextState === "on";
  document.body.classList.toggle("mirror-off", !isOn);

  if (isOn) {
    setCameraStatus("Camera: Live");
  } else if (nextState === "off-auto") {
    setCameraStatus(`Mirror: OFF (${reason || "No face for 30s"})`);
  } else {
    setCameraStatus(`Mirror: OFF (${reason || "Gesture"})`);
  }
}

function updateMotionState(hasMotion, score = 0) {
  if (!motionStateEl) {
    return;
  }

  if (hasMotion) {
    motionStateEl.textContent = `Motion: Detected (${score.toFixed(1)}%)`;
    motionStateEl.classList.add("motion-active");
  } else {
    motionStateEl.textContent = `Motion: Clear (${score.toFixed(1)}%)`;
    motionStateEl.classList.remove("motion-active");
  }
}

function updateEmotionState(label, confidence = 0) {
  if (!emotionStateEl) {
    return;
  }

  const percent = Math.max(0, Math.min(100, Math.round(confidence * 100)));
  emotionStateEl.textContent = `Emotion: ${label} (${percent}%)`;
  if (confidence >= 0.45) {
    emotionStateEl.classList.add("emotion-active");
  } else {
    emotionStateEl.classList.remove("emotion-active");
  }
}

function isOpenPalmGesture(landmarks) {
  if (!landmarks || landmarks.length < 21) {
    return false;
  }

  const tipIdx = [8, 12, 16, 20];
  const pipIdx = [6, 10, 14, 18];
  let extended = 0;

  for (let i = 0; i < tipIdx.length; i += 1) {
    if (landmarks[tipIdx[i]].y < landmarks[pipIdx[i]].y) {
      extended += 1;
    }
  }

  const spread = Math.abs(landmarks[8].x - landmarks[20].x) > 0.17;
  const upright = landmarks[0].y > landmarks[9].y;
  return extended >= 4 && spread && upright;
}

function handleGestureResults(results) {
  const now = Date.now();
  const landmarks = results?.multiHandLandmarks?.[0];

  if (!landmarks || now - lastGestureToggleAt < 3000) {
    return;
  }

  if (!isOpenPalmGesture(landmarks)) {
    return;
  }

  lastGestureToggleAt = now;
  if (mirrorPowerState === "on") {
    setMirrorPowerState("off-manual", "Hand gesture");
  } else {
    setMirrorPowerState("on", "Hand gesture");
    lastFaceDetectedAt = Date.now();
  }
}

function startNoFaceAutoSleep() {
  autoSleepTimer = window.setInterval(() => {
    if (mirrorPowerState !== "on") {
      return;
    }

    if (Date.now() - lastFaceDetectedAt >= AUTO_OFF_MS) {
      setMirrorPowerState("off-auto", "No face for 30s");
    }
  }, 1000);
}

async function startHandGestureDetection() {
  if (!window.Hands || !cameraFeedEl) {
    return;
  }

  handsDetector = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
  });

  handsDetector.setOptions({
    maxNumHands: 1,
    modelComplexity: 0,
    minDetectionConfidence: 0.65,
    minTrackingConfidence: 0.55,
  });
  handsDetector.onResults(handleGestureResults);

  gestureTimer = window.setInterval(async () => {
    if (!cameraFeedEl.videoWidth || cameraFeedEl.readyState < 2) {
      return;
    }

    try {
      await handsDetector.send({ image: cameraFeedEl });
    } catch {
      // Ignore intermittent detector frame errors.
    }
  }, 450);
}

async function loadEmotionModels() {
  if (!window.faceapi) {
    updateEmotionState("Unavailable", 0);
    return false;
  }

  try {
    const modelUri = "https://justadudewhohacks.github.io/face-api.js/models";
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(modelUri),
      faceapi.nets.faceExpressionNet.loadFromUri(modelUri),
    ]);
    emotionModelsReady = true;
    return true;
  } catch {
    updateEmotionState("Model load failed", 0);
    return false;
  }
}

function startEmotionDetection() {
  if (!cameraFeedEl || !emotionStateEl) {
    return;
  }

  emotionTimer = window.setInterval(async () => {
    if (!emotionModelsReady || cameraFeedEl.readyState < 2) {
      return;
    }

    try {
      const detection = await faceapi
        .detectSingleFace(cameraFeedEl, new faceapi.TinyFaceDetectorOptions())
        .withFaceExpressions();

      if (!detection || !detection.expressions) {
        updateEmotionState("No face", 0);
        return;
      }

      lastFaceDetectedAt = Date.now();
      if (mirrorPowerState === "off-auto") {
        setMirrorPowerState("on", "Face detected");
      }

      const entries = Object.entries(detection.expressions);
      entries.sort((a, b) => b[1] - a[1]);
      const [topEmotion, confidence] = entries[0];
      updateEmotionState(topEmotion, confidence);
    } catch {
      updateEmotionState("Unavailable", 0);
    }
  }, 2200);
}

function startMotionDetection() {
  if (!cameraFeedEl || !motionStateEl) {
    return;
  }

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });

  if (!ctx) {
    motionStateEl.textContent = "Motion: Unsupported";
    return;
  }

  canvas.width = 160;
  canvas.height = 90;
  const threshold = 12;

  motionTimer = window.setInterval(() => {
    if (cameraFeedEl.readyState < 2 || !cameraFeedEl.videoWidth) {
      return;
    }

    ctx.drawImage(cameraFeedEl, 0, 0, canvas.width, canvas.height);
    const frame = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

    if (!previousMotionSample) {
      previousMotionSample = new Uint8ClampedArray(frame);
      updateMotionState(false, 0);
      return;
    }

    let changed = 0;
    const pixelCount = canvas.width * canvas.height;

    for (let i = 0; i < frame.length; i += 4) {
      const dr = Math.abs(frame[i] - previousMotionSample[i]);
      const dg = Math.abs(frame[i + 1] - previousMotionSample[i + 1]);
      const db = Math.abs(frame[i + 2] - previousMotionSample[i + 2]);
      const delta = (dr + dg + db) / 3;
      if (delta > threshold) {
        changed += 1;
      }
    }

    previousMotionSample.set(frame);
    const ratio = (changed / pixelCount) * 100;
    updateMotionState(ratio > 4.5, ratio);
  }, 700);
}

async function startCameraBackground() {
  if (!cameraFeedEl || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setCameraStatus("Camera: Not supported in this browser");
    return;
  }

  try {
    activeStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        facingMode: "user",
      },
      audio: false,
    });
    cameraFeedEl.srcObject = activeStream;
    setCameraStatus("Camera: Live");
    startMotionDetection();
    const loaded = await loadEmotionModels();
    if (loaded) {
      startEmotionDetection();
    }
    startNoFaceAutoSleep();
    startHandGestureDetection();
  } catch (error) {
    console.error("Camera access failed", error);
    setCameraStatus("Camera: Permission denied or unavailable");
    if (motionStateEl) {
      motionStateEl.textContent = "Motion: Camera unavailable";
    }
    updateEmotionState("Camera unavailable", 0);
  }
}

window.addEventListener("beforeunload", () => {
  if (motionTimer) {
    window.clearInterval(motionTimer);
  }
  if (emotionTimer) {
    window.clearInterval(emotionTimer);
  }
  if (gestureTimer) {
    window.clearInterval(gestureTimer);
  }
  if (autoSleepTimer) {
    window.clearInterval(autoSleepTimer);
  }

  if (activeStream) {
    activeStream.getTracks().forEach((track) => track.stop());
  }
});

if (scheduleDaySelectEl && scheduleEditorEl) {
  scheduleDaySelectEl.addEventListener("change", () => {
    const day = scheduleDaySelectEl.value;
    scheduleEditorEl.value = (scheduleCache[day] || []).join("\n");
    if (scheduleSaveStatusEl) {
      scheduleSaveStatusEl.textContent = `Editing ${day}`;
    }
  });
}

if (saveScheduleBtnEl) {
  saveScheduleBtnEl.addEventListener("click", saveScheduleForSelectedDay);
}

refreshAll();
refreshScheduleEditor();
startCameraBackground();
setInterval(refreshTime, 1000);
setInterval(refreshWeather, 60000);
setInterval(refreshStatus, 10000);
setInterval(refreshSchedule, 60000);
setInterval(refreshNews, NEWS_REFRESH_MS);
