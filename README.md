# CareerBloom — Smart Resume & Job Portal

A beginner-friendly Flask + JSON-file storage full-stack project with a lavender responsive interface.

## Features
- Separate job-seeker and employer registration/login and profiles
- PDF resume upload and selectable-text extraction
- Skill coverage analysis against a chosen role
- Skill-focused multiple-choice assessment with timer and score; optional local camera preview
- Estimated role match scores based on profile skills and latest assessment
- Learning suggestions with YouTube search links and book recommendations
- Career assistant with an optional real AI provider connection (OpenAI-compatible API); rule-based fallback if no key is configured
- Original CareerBloom introduction MP4 replaces the unrelated sample clip
- Employer job posting with seat counts, applicant totals, and accept/reject/waiting decisions with recruiter notes
- Candidate job applications, duplicate-apply prevention, and per-vacancy applicant counts
- Optional camera preview with explicit permission; camera is not recorded or uploaded
- Tab visibility/fullscreen warning counter during the assessment
- Responsive layout and local-network access from a phone

## Important limitations
- Match scores are relevance estimates, not probabilities of getting hired.
- This is a starter/demo project, not a real ATS certification or live job-feed integration.
- The chatbot uses a real generative AI model when `OPENAI_API_KEY` is configured. Set `OPENAI_MODEL` (default `gpt-4o-mini`) and optionally `OPENAI_BASE_URL`. Without a key it falls back to local career guidance rules. Never place API keys in browser JavaScript or commit them to source control.
- Browsers do not allow websites to completely block opening another browser, device, or application. Tab/fullscreen changes can only be detected in limited cases.
- Camera access requires user permission and normally works on `localhost` or HTTPS. The app does not perform face recognition or claim to prove whether someone is copying.
- The preloaded company directory is illustrative, not live hiring data. Vacancies posted by registered employer accounts are actual records inside this portal. External live-job feeds require a separate trusted API integration.

## Run on Windows (VS Code)
1. Extract the ZIP file.
2. Open the `Smart_Resume_Job_Portal` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv venv
   ```
5. Activate it:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```
6. Install packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open `http://127.0.0.1:5000` in your browser.

## Open on your phone (same Wi-Fi)
1. Connect your phone and computer to the same Wi-Fi network.
2. Find the computer's IPv4 address in a second terminal:
   ```powershell
   ipconfig
   ```
   Find the IPv4 Address under the active Wi-Fi adapter (example: `192.168.1.8`).
3. Keep `python app.py` running.
4. On your phone, open `http://COMPUTER-IP:5000` (example: `http://192.168.1.8:5000`).
5. If it does not open, allow Python through Windows Firewall for private networks and confirm both devices are on the same Wi-Fi.

The app listens on `0.0.0.0:5000` for local network testing. Do not expose this development server directly to the public internet.

## First use
- Register a student account.
- Open My Profile and choose a role, education and skills.
- Upload a text-based PDF resume.
- Take the role assessment.
- Review Job Matches and Learning Hub.
- Add opportunities to Application Tracker.

## Data and reset
User accounts, assessment results and applications are stored in `portal_data.json`; uploaded resumes are stored in `uploads/`. To reset your demo data, stop the server and delete `portal_data.json` and the files inside `uploads/`.


## New: Resume Builder
After signing in, open **Resume Builder** from the navigation. Fill in your contact details, summary, education, projects, experience, skills and certifications, then press **Download my resume as PDF**. Follow the on-page guidelines and review the PDF before applying.

## Open the app on your phone (same Wi-Fi)
1. Keep the Flask app running on your computer with `python app.py`.
2. Connect your phone and computer to the same Wi-Fi network. A phone cannot use the computer-only address `127.0.0.1`.
3. On the computer, open PowerShell in a second terminal and run `ipconfig`. Under the active Wi-Fi adapter, find **IPv4 Address** (for example `192.168.1.8`).
4. On the phone, open Chrome and enter `http://192.168.1.8:5000`, replacing the example with your computer's actual IPv4 address. Do not type `127.0.0.1` on the phone.
5. If it still does not load, allow Python through Windows Defender Firewall on **Private networks** and confirm both devices are on the same Wi-Fi (not guest Wi-Fi). Keep the computer awake and the Flask terminal running.
6. If the address starts with `169.254`, the computer may not be connected properly to the Wi-Fi network. Reconnect and run `ipconfig` again.

The app binds to `0.0.0.0` for local-network access. This is a development project; do not expose the Flask development server directly to the public internet.

## Storage note
This project does **not** require MongoDB or a separately installed SQLite database. It stores app data in `portal_data.json` using Python's built-in JSON module. Keep this file with `app.py`; back it up to preserve registered accounts and progress. Uploaded resumes are stored in `uploads/`.

## Company directory note
The current demo directory contains 552 generated sample employer-name entries distributed across job sectors. They are demonstration records, **not 552 verified real companies or live vacancies**. Replace them with a sourced employer dataset before using this as a real job board.

## AI assistant setup (optional)
PowerShell example for the current terminal session:
```powershell
$env:OPENAI_API_KEY="your-provider-api-key"
$env:OPENAI_MODEL="gpt-4o-mini"
python app.py
```
The key stays on the server. With a valid key configured, the chatbot can answer open-ended questions through the configured AI provider. Without a key, only limited built-in career guidance is available; it cannot answer arbitrary questions.

## Employer workflow
1. Register and choose **Employer / Admin**. Enter the company name.
2. Post a vacancy with its title, category, required skills and number of seats.
3. Candidates can find the vacancy under **Job Matches** and apply once.
4. The employer dashboard shows applicant totals and candidate details. Set each application to **Accepted**, **Rejected** or **Waiting**, and optionally add a note.

## Candidate workflow
1. Register as a **Job seeker**, add education and skills.
2. Complete the skill-focused quiz. Saving skills in My Profile opens the quiz immediately. The quiz stays locked until camera permission is granted; the camera preview runs locally and no video is recorded or uploaded. Resume Builder also has a separate “Save skills & start quiz” action.
3. Upload a PDF resume, review skill gaps, and explore job match percentages.
4. Apply to employer-posted vacancies and ask the Career Assistant for skill-improvement suggestions.


## Quiz camera and browser mode
The quiz requires camera permission before displaying questions. A website cannot force Chrome or another browser to launch in Incognito/Private mode; browser privacy modes are controlled by the user. To use a private window, open it yourself (for Chrome on Windows: Ctrl+Shift+N), visit `http://127.0.0.1:5000`, sign in, and allow camera access when prompted. The browser may remember or separately ask for camera permission in private mode.
