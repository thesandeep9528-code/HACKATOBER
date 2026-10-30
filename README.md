<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Outfit&weight=800&size=42&pause=1000&color=22C55E&center=true&vCenter=true&width=700&height=80&lines=%F0%9F%8C%BF+AgriSmart+AI;FieldGuard+Platform;SIH+2026+%7C+Problem+Statement+1" alt="AgriSmart AI FieldGuard" />

<br/>

<p align="center">
  <img src="https://img.shields.io/badge/SIH--2026--Internal--Hackathon-22c55e?style=for-the-badge&logo=trophy&logoColor=white" />
  <img src="https://img.shields.io/badge/LJIET-Institution-16a34a?style=for-the-badge&logo=mortarboard&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/AI%2FML-EfficientNet--B4-a855f7?style=for-the-badge&logo=tensorflow&logoColor=white" />
  <img src="https://img.shields.io/badge/Tests-17%2F17%20Passing-4ade80?style=for-the-badge&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/PyTorch-2.0-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" />
</p>

<br/>

> **A farmer-first, AI-powered crop disease diagnosis and smart farm advisory platform.**
> Built for the **SIH 2026 Internal Hackathon — Problem Statement 1: AGRISMART AI**.
> *The image classifier is the strict source of truth. No dashboard feature can overwrite a disease label.*

</div>

---

## 🎬 Demo Video

> **Watch FieldGuard in action** — disease detection, irrigation advisory, crop recommendation, community forum, and AI chatbot, all in one seamless flow.

<div align="center">

[![Watch the Demo ▶](docs/Cover-preview-photo-for-video-display.png)](https://drive.google.com/file/d/1wgkK8VPVlKL9BEq5k79xQ0xYlaEQAq2D/view?usp=drivesdk)

**[▶ Watch Full Demo on Google Drive](https://drive.google.com/file/d/1wgkK8VPVlKL9BEq5k79xQ0xYlaEQAq2D/view?usp=drivesdk)**

</div>

---

## 🖼️ Project Posters

<div align="center">

<img src="docs/infographical-poster.png" alt="Infographical Poster" width="60%" />
<br/><sub><b>Infographical Poster</b></sub>

<br/><br/>

<img src="docs/informative-poster.png" alt="Informative Poster" width="100%" />
<br/><sub><b>Informative Poster</b></sub>

</div>

---

## 📌 Table of Contents

- [The Problem We Solve](#-the-problem-we-solve)
- [Solution Architecture](#-solution-architecture)
- [Key Metrics](#-key-metrics)
- [Feature Showcase](#-feature-showcase)
- [Real-World Testing](#-real-world-testing)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Platform Subsystem Tests](#-platform-subsystem-tests)
- [Project Structure](#-project-structure)

---

## 🌾 The Problem We Solve

India loses **₹90,000 crore+** annually to undetected crop diseases. Small and marginal farmers — who make up **86% of India’s farming community** — lack access to:

- Expert agronomists for timely disease diagnosis
- Data-driven irrigation guidance calibrated to their specific crops
- Science-backed crop selection recommendations
- A community of peers and AI assistance in their language

**FieldGuard bridges this gap** by putting a lab-grade AI model directly in a farmer’s pocket, backed by a full smart farm advisory stack.

---

## 🏗️ Solution Architecture

```mermaid
flowchart TD
    subgraph INPUT["📱 Farmer Input"]
        A1[📷 Image Upload]
        A2[🌐 Webcam Capture]
        A3[📡 ESP32-CAM IoT]
    end

    subgraph ML["🧠 Core ML Engine — EfficientNet-B4"]
        B1[🛡️ Quality Gate\nfoliage pixel check]
        B2[🔬 Disease Classifier\n38-class · 98.73% accuracy]
        B3[📊 Calibration + GradCAM\ntop-3 confidence · heatmap]
    end

    subgraph ADVISORY["⚙️ Advisory Context Layer"]
        C1[💧 Smart Irrigation\nWeather-aware · Sustainability Score]
        C2[🌱 Crop Recommendation\nRandom Forest · NPK + pH]
        C3[📈 Farm Operations\nGrowth Stage · Alert Engine]
    end

    subgraph FARMER["👨‍🌾 Farmer-Facing Layer"]
        D1[🤖 AI Chatbot\nGPT-4 Grounded]
        D2[👥 Community Forum\nPost · Answer · Upvote]
        D3[📄 PDF Reports\nFarm Health Export]
    end

    A1 & A2 & A3 --> B1
    B1 -->|✅ Valid Plant Image| B2
    B1 -->|❌ Rejected| E([Non-Plant Warning])
    B2 --> B3
    B3 -->|Disease Label\nsource of truth| C1 & C2 & C3
    C1 & C2 & C3 --> D1 & D2 & D3

    style INPUT fill:#14532d,color:#fff,stroke:#22c55e
    style ML fill:#1e3a5f,color:#fff,stroke:#3b82f6
    style ADVISORY fill:#3b1f5e,color:#fff,stroke:#a855f7
    style FARMER fill:#7c2d12,color:#fff,stroke:#f97316
    style E fill:#7f1d1d,color:#fff,stroke:#ef4444
```

### Core Architectural Principle

> **The image classifier is the immutable source of truth for plant pathology.**
> Farm sensor context enriches irrigation recommendations and sustainability metrics — but **never modifies or overwrites the predicted disease label.**

---

## 📊 Key Metrics

<div align="center">

| Metric | Value |
|:-------|:------|
| 🎯 Validation Accuracy | **98.73%** |
| 📐 Macro-F1 Score | **97.97%** |
| 🌿 Disease Classes | **38 (PlantVillage + PlantDoc)** |
| 🖼️ Training Images | **45,770** |
| ✅ Validation Images | **11,079** |
| 🔬 GPU | **NVIDIA RTX 4050 (AMP fp16)** |
| 🧪 Subsystem Tests | **17 / 17 Passing (100%)** |
| 🔒 Cross-Split Leakage | **Zero (SHA-256 verified)** |

</div>

### Training History

| Epoch | Training Loss | Val Macro-F1 | Val Accuracy | Notes |
|:-----:|:-------------:|:------------:|:------------:|:------|
| **1** | 0.7349 | 97.49% | 98.31% | Lab representation initial fit |
| **2** | 0.6373 | **97.97%** | **98.73%** | ⭐ Top validation checkpoint |
| **3** | 0.6575 | 97.75% | 98.59% | Convergence checkpoint |
| **4** | 0.6389 | 97.94% | 98.71% | PlantDoc in-field integration + RandomErasing |
| **5** | 0.6381 | 97.87% | 98.67% | Cosine annealing fine-tuning (LR = 3x10^-5) |

---

## ✨ Feature Showcase

### 🔬 1. AI Disease Detection (Core Module)

- **EfficientNet-B4** fine-tuned on **56,849 images** (PlantVillage + PlantDoc combined)
- **Quality Gate** — rejects non-plant images before inference (foliage pixel check)
- **Calibrated confidence** with top-3 alternatives and traceable GradCAM heatmaps
- **Versioned precaution guidance** — actionable, crop-specific treatment protocols
- **ESP32-CAM integration** — farmers in low-connectivity areas can use IoT cameras
- Input: `/disease_detection` → Upload or webcam → Instant diagnosis + treatment plan

### 💧 2. Smart Irrigation Advisory

- **Weather-aware rule engine** — integrates rainfall forecast, soil moisture, temperature
- **Crop-stage aware** — thresholds adapt to growth stage (seedling vs. mature)
- **Full decision trace** — every `IRRIGATE_NOW` or `DELAY_IRRIGATION` verdict is auditable step-by-step
- **Sustainability Score** — reproducible formula quantifying water efficiency per decision
- Demo: Soil `18%`, Temp `36°C`, Rain `0mm` → `IRRIGATE_NOW` (Score: 35)

### 🌱 3. ML Crop Recommendation

- **Random Forest Classifier** trained on real NPK-pH-climate data
- Input: N, P, K, pH, temperature, humidity, rainfall → Recommended crop
- Returns **split fertilizer schedule** and **water need estimate**
- 1-click **"Add to My Farms"** creates a farm and begins tracking

### 📈 4. Crop Tracking & Farm Operations Dashboard

- **Growth stage progress tracker** with phase-aware benchmarks
- **Sensor Scout** — logs field observations (LCC, pest sightings, yield estimates)
- **Alert Engine** — auto-triggers `Nitrogen Deficiency` advisory when LCC < threshold
- **Disease badge** on every farm — linked directly to the AI diagnosis log

### 👥 5. Farmer Community Forum

- Post questions, submit answers, upvote best responses
- Threaded discussions organized by crop type and disease category

### 🤖 6. Agronomy AI Chatbot

- **GPT-4 grounded** with agronomic context — not a generic chatbot
- Accessible via bottom-right widget on any page

### 📄 7. Farm Report Export

- One-click **PDF export** of complete farm health report
- Includes diagnosis history, irrigation log, sustainability scores, and growth timeline

---

## 🌍 Real-World Testing Results

Tested on **real-world images** from Google & Wikimedia — never seen during training:

| Crop & Disease | AI Prediction | Confidence | Result |
|:--------------|:-------------|:----------:|:------:|
| Grape Black Rot | `Grape___Black_rot` | **96.2%** | ✅ Correct |
| Northern Corn Leaf Blight | `Corn___Northern_Leaf_Blight` | **88.9%** | ✅ Correct |
| Tomato Septoria Leaf Spot | `Tomato___Septoria_leaf_spot` | 51.8% | ✅ Correct |
| Potato Late Blight | `Potato___Late_blight` | 44.0% | ✅ Correct |
| Tomato Late Blight | `Tomato___Late_blight` | 33.3% | ✅ Correct |
| Healthy Citrus Foliage | `Healthy Foliage` | **92.1%** | ✅ Correct |
| Laptop (Non-plant) | `Non-Plant / Unclear` | 0.0% | 🛡️ Quality Gate Rejected |

> **7 / 7 correct** — including a non-plant image properly rejected by the Quality Gate.

---

## 🧪 Platform Subsystem Tests

All 17 platform subsystems pass in a fully headless environment:

```
================================================================================
  AGRISMART AI - COMPLETE HEADLESS SYSTEM & FEATURE TEST SUITE
  Real Google/Web Photos . Quality Gate . Irrigation . ML . Farm Ops . Chat
================================================================================

[TEST  1] Demo Authentication & Session Initialization .............. PASS
[TEST  2] Leaf Disease AI on Real-World Google/Web Images ........... PASS  (8/8)
[TEST  3] Quality Gate & Non-Plant Image Rejection .................. PASS
[TEST  4] Smart Irrigation Advisory (Rules + Sustainability) ........ PASS
[TEST  5] ML Crop Recommendation (Random Forest Classifier) ......... PASS
[TEST  6] 1-Click Farm Creation from Prediction ..................... PASS
[TEST  7] Disease Diagnosis Logging to Farm Timeline ................ PASS  (+10 HP)
[TEST  8] Crop Standards & Sensor Scout Benchmark Alerts ............ PASS
[TEST  9] Farmer Community Forum (Post, Answer, Upvote) ............. PASS
[TEST 10] Agronomy AI Chatbot Assistant ............................. PASS

================================================================================
  TEST RESULTS: 17 / 17 Subsystems & Tests PASSED (100.0%)
================================================================================
```

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|:------|:-----------|
| **Web Framework** | Flask 3.0 + Flask-SQLAlchemy |
| **ML / CV** | PyTorch 2.0, TorchVision, EfficientNet-B4 |
| **Crop ML** | Scikit-Learn (Random Forest), Pandas, NumPy |
| **AI Assistant** | OpenAI GPT-4 (grounded agronomic context) |
| **Database** | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy |
| **Training** | AMP fp16, CosineAnnealingLR, Mixed Precision |
| **Image Augmentation** | TorchVision v2 (ColorJitter, GaussianBlur, RandomErasing) |
| **Report Export** | ReportLab, xhtml2pdf, pdfkit |
| **Auth** | Flask-Login, Werkzeug password hashing |
| **Dataset** | PlantVillage (lab) + PlantDoc (in-field, 56,849 total) |
| **IoT** | ESP32-CAM `/capture` integration |

</div>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended) or CPU

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/Kuldeeep18/AgriSmart_AI.git
cd AgriSmart_AI

# 2. Create and activate virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open **`http://127.0.0.1:5144`**. The app uses a local SQLite database by default. Login and sign-up do not require OTP; Gmail SMTP is only needed for password recovery.

### Website languages

Use the language selector on the site to display pages in English, Hindi,
Telugu, Tamil, Kannada, Malayalam, or Bengali. Your selection is saved in this
browser. Translation is provided by Google Translate and requires an internet
connection; page text is sent to Google for translation.

### New-user feature tour

After a new user signs up, the dashboard tour first asks them to choose English,
Hindi, Telugu, Tamil, Kannada, Malayalam, or Bengali. Tour instructions are translated into that language; translation
requires an internet connection. The guided tour highlights the main farming
tools and chatbot, then offers hands-on lessons for crop recommendations,
irrigation, and leaf diagnostics. Numeric examples and dropdown selections can
be applied to the form for practice, but the tutorial does not submit forms or
run a diagnosis. Values are examples only and should be replaced with actual
soil tests, field measurements, and local forecasts. Choose **Skip learning**
at any time to end the tour immediately. Completion or skipping is saved in
that browser for the signed-in account. Refreshing the dashboard does not start
the tour again. Existing users can restart it using **Learn again** below their
profile in the navbar.
To replay the tour from the beginning, choose **Learn again** below **Profile**
in the account menu.

### Chatbot farmer FAQs

The chatbot includes 100 searchable, offline farmer FAQs covering soil,
seeds, irrigation, nutrients, pests, plant diseases, crop care, harvest, and
farm safety. Open the chatbot and choose **Farmer FAQs** to search and submit
a question. Review pesticide, disease, and crop-specific advice with your
local agriculture extension service before acting.

The chatbot also supports voice questions and spoken answers. If browser speech
recognition is unavailable, voice input is transcribed locally with the
multilingual Whisper Small model; no speech API key is required and recordings
are not sent to a cloud transcription service. The first voice request
downloads the model (about 460 MB) and requires internet access; subsequent
transcription runs locally. Set `WHISPER_MODEL` in `.env` to `tiny` for a
smaller, less accurate model. Microphone permission is required. Spoken replies
are translated to the selected language with Google Translate and require an
internet connection; the reply text is sent to Google for translation. The
browser or operating system must provide a speech voice for the selected
language.

### Password recovery email setup

Login and sign-up go directly to the dashboard without an OTP step. Forgot
password still uses an email OTP and requires Gmail SMTP credentials. Copy
`.env.example` to `.env`, set
`MAIL_USERNAME` to your Gmail address and `MAIL_PASSWORD` to a Google App
Password (not your regular Gmail password), then restart the app. Google
requires 2-Step Verification to create an App Password. If delivery fails,
check the app's terminal output for the SMTP error.

### ML Commands

```powershell
# Train the disease classifier
py -m model.train --train-dir data/train --val-dir data/val --output-dir artifacts/run-001

# Evaluate (macro-F1, confusion matrix, per-class metrics)
py -m model.evaluate --weights artifacts/run-001/best_model.pt --class-names artifacts/run-001/class_names.json --data-dir data/val --output-dir artifacts/run-001/evaluation

# Single-image prediction (the SIH-required interface)
py -m model.predict --image path\to\leaf.jpg --weights artifacts/run-001/best_model.pt --class-names artifacts/run-001/class_names.json
```

### Feature Walkthrough (Browser)

| Feature | URL | How to Test |
|:--------|:----|:------------|
| Disease Detection | `/disease_detection` | Upload any leaf from `downloaded_from_google/` |
| Quality Gate | `/disease_detection` | Upload `test_non_plant_laptop.jpg` — rejected! |
| Irrigation | `/crop_tracking` | Soil `18%`, Temp `36°C`, Rain `0mm` → `IRRIGATE_NOW` |
| Crop Recommendation | `/crop_prediction` | N=90, P=42, K=43, pH=6.5 → ML predicted crop |
| Farm Dashboard | `/crop_tracking` | Log LCC=2 → Nitrogen alert fires |
| Community | `/farmer_community` | Post, answer, upvote |
| Chatbot | Any page | Bottom-right widget |

---

## 📁 Project Structure

```
lj_internal/
├── app.py                    # Flask application factory & routes
├── auth.py                   # Authentication (login, register, sessions)
├── chatbot.py                # GPT-4 agronomy chatbot
├── community.py              # Farmer community forum
├── config.py                 # App configuration & env vars
├── crop_prediction.py        # Random Forest crop recommendation
├── crop_tracking.py          # Farm operations & alert engine
├── disease_detection.py      # Core AI disease detection routes
├── models.py                 # SQLAlchemy ORM models
├── model/
│   ├── train.py             # EfficientNet-B4 training (AMP fp16)
│   ├── predict.py           # predict(image_path) — SIH interface
│   ├── evaluate.py          # Macro-F1, confusion matrix, per-class
│   ├── gradcam.py           # GradCAM explainability heatmaps
│   ├── prepare_plantvillage.py  # 80/20 stratified split (seed 2026)
│   └── prepare_plantdoc.py      # PlantDoc in-field integration
├── artifacts/                # Trained model checkpoints & metadata
├── templates/                # Jinja2 HTML templates
├── tests/                    # Headless test suite (17/17)
├── docs/
│   ├── demo-preview.jpg      # Demo thumbnail
│   ├── WALKTHROUGH.md        # Complete implementation walkthrough
│   └── infographical-poster.png
└── requirements.txt
```

---

<div align="center">

**Built with 🌿 for India's farmers**

*AgriSmart AI FieldGuard — SIH 2026 | LJIET*

</div>
