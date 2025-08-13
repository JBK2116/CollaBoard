
# CollaBoard — Real-Time Meeting & Summary Platform

**Live Demo:** [collaboard.site](https://collaboard.site)

---

## 📖 Overview

CollaBoard is a lightweight, real-time meeting application inspired by a family game night conversation. The goal was to make an app that is able to create and join meetings in under 2 minutes, have participants respond to open-ended questions, and instantly summarize the results with AI.

Unlike traditional meeting tools, CollaBoard is designed for **quick, recreational sessions** rather than corporate or sensitive data. It’s fast, accessible, and requires no complicated setup.

---

## 🎯 Key Features

* **Real-time Kahoot-style meetings** with open-ended questions and text answers.
* **Instant meeting creation** — from idea to live in under 2 minutes.
* **Flexible durations** — 1 minute to 1 hour.
* **Manual or automatic meeting termination**.
* **AI-powered summaries** (OpenAI GPT-4o mini).
* **One-click export** to PDF or DOCX.
* **Secure authentication** for hosts.
* **Fully deployed on AWS EC2 with custom domain**.

---

## 🛠 Tech Stack

**Frontend:** HTML, CSS, Vanilla JavaScript

**Backend:** Django

**Real-time Communication:** WebSockets

**ASGI Server:** Daphne (handles both HTTP & WebSocket traffic)

**AI Integration:** OpenAI API (GPT-4o mini)

**Deployment:** AWS EC2, Nginx (reverse proxy)

**Exporting:** ReportLab (PDF), python-docx (DOCX)

---

## 🏗 Architecture Overview

1. **Client Side (Browser)** — HTML, CSS, and vanilla JavaScript for UI rendering and user interactions.
2. **Django Backend (ASGI)** — Handles authentication, meeting creation, WebSocket events, AI summarization, and export features.
3. **Daphne** — Primary ASGI server managing both HTTP requests and WebSocket connections.
4. **Nginx** — Reverse proxy that terminates SSL, serves static files, and forwards HTTP/WebSocket traffic to Daphne.
5. **OpenAI API Layer** — Processes meeting responses into summaries via GPT-4o mini.
6. **AWS EC2 Hosting** — Runs the application with `systemd`-managed Daphne and Nginx services.

---

## 🖥 Production Infrastructure

* **Hosting:** AWS EC2 (Ubuntu)
* **Server Process Management:** `systemd` for Daphne & Nginx services
* **Reverse Proxy:** Nginx handles SSL termination, static files, and WebSocket upgrade requests
* **SSL/TLS:** Let’s Encrypt certificate enforcing **HTTPS** for web traffic and **WSS** for WebSockets
* **Domain:** Custom domain `collaboard.site` configured via Namecheap DNS
* **Security:** HTTP traffic automatically redirected to HTTPS; WebSocket connections only allowed over WSS
* **Static Files:** Served directly via Nginx for performance

---

## 📸 Screenshots / Demo

**Demo Video Coming Soon** —> For now, try it live: [collaboard.site](https://collaboard.site)

---

## ⚠ Known Limitations / Future Improvements

* Host or participant disconnect mid-meeting currently ends their session. Planned enhancement: **graceful reconnection support**.
* No meeting persistence — sessions and summaries are deleted shortly after use.

---

## 📜 License / Usage

© 2025 CollaBoard. All rights reserved.

The source code may be **viewed for educational purposes only**. Modification, redistribution, or commercial use is **not allowed**.

