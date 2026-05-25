# NFL Edge: Front Office Analytics OS

![NFL Edge](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Python](https://img.shields.io/badge/Backend-Python_3.10+-blue.svg)
![Next.js](https://img.shields.io/badge/Frontend-Next.js_16-black.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57.svg)

**NFL Edge** (formerly Intelligence Command Center) is a full-stack, data-driven operating system designed for NFL front offices, analysts, and coaching staffs. It bridges the gap between raw play-by-play data and actionable on-field strategy by mathematically evaluating team performance across three specialized engines.

---

## 🏈 The Three Pillars of Analysis

1. **Play-Calling Efficiency & Predictability Engine**
   - Evaluates offensive coordination by comparing pass/run tendencies against dynamic league-wide baselines.
   - Computes mathematically optimal 4th-down decision making, factoring in late-game win probability leverage.

2. **Roster Value (VOR) & Cap Engine**
   - Optimizes General Manager performance by mapping player Expected Points Added (EPA) to their current salary cap hit.
   - Calculates positional Value Over Replacement (VOR) using a strict 55th-percentile starter baseline to identify overpaid veterans and underpaid draft steals.

3. **In-Game Decision & Game Management Engine**
   - Grades the Head Coach on critical game management scenarios.
   - Penalizes wasted timeouts while preserving strategic late-half clock stoppages.
   - Quantifies clutch performance leverage in one-score games during the 4th quarter.

---

## 🏗️ Technical Architecture

This project is split into two distinct environments: a **Python Data Pipeline** for raw metric processing, and a **Next.js Web Frontend** for data visualization.

- **Data Engineering**: Python, Pandas, NumPy
- **Database**: SQLite3
- **Frontend Framework**: Next.js 16 (App Router), React, TypeScript
- **Styling & UI**: Tailwind CSS v4, WebGL Shaders (via `@paper-design/shaders-react`), Glassmorphism aesthetics
- **Charting**: D3.js concepts and Recharts

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**

### 1. Backend: Running the Data Pipeline
The backend ingests raw play-by-play data, runs the 3 analytical engines, and exports the finalized calculations as static JSON files to the frontend.

```bash
# Clone the repository
git clone https://github.com/yourusername/nfl-edge.git
cd nfl-edge

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install pandas numpy sqlite3

# Run the 3 analytical engines and export the data to the dashboard
python -m src.engines.roster_value
python -m src.engines.play_calling
python -m src.engines.in_game_decisions
python src/export_data.py
python dashboard/public/data/recalculate_5_metrics_v3.py
```

### 2. Frontend: Running the Web Application
The frontend is a sleek, modern Next.js application that visualizes the static JSON data exported by the backend.

```bash
# Navigate to the dashboard directory
cd dashboard

# Install frontend dependencies
npm install

# Start the local development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the application.

---

## 🌐 Deployment (Vercel)

When deploying this project to Vercel, please ensure you configure the **Root Directory** setting to `dashboard` instead of `./` (the root). Because the Next.js application lives inside the `dashboard/` directory, Vercel needs to be explicitly pointed there to successfully build the site.

---

## 📄 License
This project is for educational and analytical purposes. NFL data belongs to the National Football League.
