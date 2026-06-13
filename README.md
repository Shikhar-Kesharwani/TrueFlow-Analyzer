<div align="center">
  <h1>🚀 TrueFlow-Analyzer</h1>
  <p><strong>Next-Generation Deep Packet Inspection (DPI) & Telemetry Engine</strong></p>
  
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Machine_Learning-FF6F00?style=for-the-badge&logo=scikitlearn&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" />
</div>

<br />

## 📸 Dashboard Preview

> **Note:** Add a screenshot of your beautiful React Dashboard here by dragging and dropping an image into GitHub!
> 
> *[Placeholder: Example Dashboard Screenshot]*
> `![Dashboard Screenshot](link-to-your-image-here.png)`

---

## 📖 Overview

TrueFlow-Analyzer is a modern, real-time Deep Packet Inspection (DPI) system built to track **actual user activity** while bypassing modern network encryption like DNS-over-HTTPS (DoH) and QUIC.

Unlike traditional packet sniffers (like Wireshark) that blindly report every single network ping, TrueFlow-Analyzer incorporates a smart **Noise-Cancellation Engine**. 

### 🎧 The "Background Noise" Filter
If you leave your phone locked on a desk, apps like Facebook, Instagram, and WhatsApp are constantly sending tiny telemetry pings to their servers. A basic sniffer will falsely report that you are actively using these apps.

**TrueFlow-Analyzer solves this.** It uses intelligent IP/DNS subnets combined with **bandwidth thresholding heuristics** (e.g., >40,000 byte payloads) to mathematically distinguish between a background sync ping and an active user session (like watching a video or scrolling a feed). The background noise is intentionally filtered out.

---

## ✨ Key Features

- **Real-Time Active Tracking:** The React dashboard only lights up when an app is actually being engaged by a human.
- **Noise-Cancellation Engine:** Background telemetry to Google and Meta servers is automatically suppressed.
- **DoH & QUIC Bypass:** Uses static IP subnet mapping to reliably identify apps (WhatsApp, Instagram, YouTube) even when DNS requests are fully encrypted.
- **Hybrid ML Classification:** Employs a Random Forest Machine Learning model alongside deterministic IP rules for legacy protocols.
- **Smooth React Dashboard:** Features an exponential decay algorithm for a seamless, flicker-free UI monitoring experience.

---

## 📂 Repository Structure

```text
TrueFlow-Analyzer/
├── live_dpi_engine.py         # Main Python Packet Sniffer & ML Engine
├── sniff.py                   # Lightweight CLI network sniffer for debugging
├── dashboard/                 # React.js Vite Frontend
│   ├── src/
│   │   ├── App.jsx            # Main dashboard UI component
│   │   ├── index.css          # Beautiful glassmorphism styling
│   │   └── ...
├── dashboard-server/          # Node.js WebSocket Broker API
│   └── server.js              # Express + Socket.io Server
├── ml/                        # Machine Learning Model Generators
│   ├── train_model.py         # Random Forest training script
│   └── ...
├── .github/                   # GitHub Issue Templates
├── CONTRIBUTING.md            # Guidelines for open-source contributors
├── LICENSE                    # MIT Open Source License
└── README.md                  # This file
```

---

## 🏗️ System Architecture

The system is composed of three interconnected layers:

1. **Python DPI Engine (`live_dpi_engine.py`):** Captures live packets via `scapy`, evaluates traffic volume, applies ML/IP classification logic, and drops noise.
2. **Node.js API (`dashboard-server`):** Acts as a high-speed broker, receiving telemetry from the engine and pushing it via WebSockets.
3. **React.js Dashboard (`dashboard`):** A beautifully crafted, responsive frontend using Vite and modern UI paradigms.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** (with `scapy`, `scikit-learn`, `pandas`)
- **Node.js 18+**
- **Npcap** (Windows) or **libpcap** (Linux) for packet capturing.

### Installation & Execution

#### 1. Start the DPI Engine
Open a terminal as Administrator/root:
```bash
git clone https://github.com/AyushGU12/TrueFlow-Analyzer.git
cd TrueFlow-Analyzer
python live_dpi_engine.py --mode live
```

#### 2. Start the Node.js API Broker
Open a second terminal:
```bash
cd dashboard-server
npm install
node server.js
```

#### 3. Launch the React Dashboard
Open a third terminal:
```bash
cd dashboard
npm install
npm run dev
```

Visit `http://localhost:5173` in your browser to view the live dashboard!

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check out the [issues page](../../issues). Read our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## 🛡️ Privacy & Security

This tool analyzes network metadata (IP, SNI, bandwidth volume) to classify applications. It does **not** decrypt HTTPS payloads or capture private user data. It is built strictly for telemetry, network analysis, and educational purposes.

---
<div align="center">
  <i>Built with ❤️ by <a href="https://github.com/AyushGU12">AyushGU12</a> to make network analysis smarter.</i>
</div>
