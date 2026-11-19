document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("testForm");
  const cameraBtn = document.getElementById("cameraBtn");
  if (form && cameraBtn) {
    let seconds = 600, submitted = false, warnings = 0, stream = null;
    const video = document.getElementById("cameraPreview");
    const status = document.getElementById("cameraStatus");
    const locked = document.getElementById("quizLocked");
    const timer = document.getElementById("timer");
    const warning = document.getElementById("tabWarnings");
    cameraBtn.addEventListener("click", async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        status.textContent = "Camera access is unavailable. Open the site using http://127.0.0.1:5000 or HTTPS in a supported browser.";
        return;
      }
      cameraBtn.disabled = true; status.textContent = "Waiting for camera permission…";
      try {
        stream = await navigator.mediaDevices.getUserMedia({video: true, audio: false});
        video.srcObject = stream; video.style.display = "block";
        status.textContent = "Camera is active. Your quiz has started; video is not recorded or uploaded.";
        cameraBtn.textContent = "Camera active";
        locked.style.display = "none"; form.style.display = "block";
        let interval = setInterval(() => {
          if (submitted) { clearInterval(interval); return; }
          seconds--; timer.textContent = `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`;
          if (seconds <= 0) { submitted = true; form.submit(); }
        }, 1000);
        document.addEventListener("visibilitychange", () => {
          if (document.hidden && !submitted) { warnings++; warning.textContent = `Tab-switch warnings: ${warnings}`; }
        });
        document.addEventListener("fullscreenchange", () => {
          if (!document.fullscreenElement && !submitted) { warnings++; warning.textContent = `Tab-switch / fullscreen warnings: ${warnings}`; }
        });
        form.addEventListener("submit", () => { submitted = true; });
      } catch (e) {
        cameraBtn.disabled = false;
        status.textContent = "Camera permission is required to start. Allow camera access in your browser settings, then try again.";
      }
    });
    window.addEventListener("beforeunload", () => { if (stream) stream.getTracks().forEach(t => t.stop()); });
  }
  const chatForm = document.getElementById("chatForm");
  if (chatForm) {
    const messages = document.getElementById("chatMessages"), input = document.getElementById("chatText");
    chatForm.addEventListener("submit", async e => {
      e.preventDefault(); const message = input.value.trim(); if (!message) return;
      const userBubble = document.createElement("div"); userBubble.className="bubble user"; userBubble.textContent=message; messages.appendChild(userBubble); input.value="";
      const wait = document.createElement("div"); wait.className="bubble bot"; wait.textContent="Thinking…"; messages.appendChild(wait); messages.scrollTop=messages.scrollHeight;
      try {
        const res = await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message})});
        const data = await res.json(); wait.textContent=data.reply || "Please try again.";
      } catch { wait.textContent="Could not reach the server. Please try again."; }
      messages.scrollTop=messages.scrollHeight;
    });
  }
});
