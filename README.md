# 💰 Smart Personal Finance Manager

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Standard_Library-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%7C%20CSS3%20%7C%20ES6%2B-E34F26.svg?logo=html5&logoColor=white)](https://developer.mozilla.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4.1-FF6384.svg?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, full-stack personal finance application built with **FastAPI**, **SQLite**, and a zero-build **HTML/CSS/Vanilla JavaScript** frontend. Designed around Indian Rupee (`₹`) formatting (`en-IN`) with a custom emerald and gold aesthetic.

---

## 🌟 Key Features

### 1. 📊 Income & Expense Tracking
- Add, view, filter, and delete transactions on a month-by-month basis.
- **Strict Alphabet-Only Validation**: Description, category, and name fields strictly allow only alphabets and spaces, actively preventing accidental or arbitrary numeric inputs.
- **Bulk CSV Import**: Import bank transaction records with auto-sanitization (`date`, `description`, `amount`, `type`, `category`).

### 2. 🤖 Rule-Based Auto-Categorization
- Automatic keyword classification engine maps merchant text to categories (e.g. `Swiggy` / `Zomato` → **Food**, `Uber` / `Ola` → **Transport**, `BESCOM` / `Recharge` → **Bills**).
- Leaving the category blank defaults to automated categorization.

### 3. 🎙️ Quick Add & Voice Recognition
- Natural-language transaction recording: type or speak *"Spent 250 on lunch"* to automatically parse the amount and category.
- Integrated with the native browser **Web Speech API** for hands-free voice expense logging.

### 4. 🎯 Smart Cutoff Engine & Budgets
- Set monthly spending caps per category with visual warnings at **80%** and **100%** utilization.
- **Smart Cutoff Suggestion**: Calculates historical 3-month spending averages and suggests recommended targets reduced by 10%.
- **Daily Spending Allowance**: Live hero metric computing `(Remaining Budget) / (Days Left in Month)` so you always know your safe daily spending limit.

### 5. 💳 Debt Payoff Modeling (Avalanche vs. Snowball)
- Comprehensive debt tracker tracking loan balances, interest rates, and minimum monthly payments.
- **Interactive Simulator**: Compares minimum payments against **Debt Avalanche** (highest interest first) and **Debt Snowball** (lowest balance first).
- **Extra Payment Slider**: Visualizes total interest saved and months cut off your debt-free date.
- Gracefully handles underwater loans where payments fail to cover monthly accrued interest.

### 6. 🧮 Built-in Financial Calculators
- **EMI Calculator**: Equated Monthly Installment calculation with total interest and payment breakdown.
- **Simple vs. Compound Interest**: Side-by-side comparison with monthly compounding options.

### 7. 📈 Intelligent Financial Health & Anomaly Detection
- **Financial Health Score (0–100)**: Composite index based on savings rate (40%), debt-to-income ratio (30%), and budget discipline (30%).
- **Statistical Anomaly Detection**: Highlights spending anomalies greater than $\mu + 2\sigma$ and detects duplicate charges.
- **Recurring Subscription Detector**: Identifies recurring monthly debits across multiple billing cycles (e.g. Netflix, Spotify).

### 8. 🏆 Financial Goals Tracker
- Create savings targets with target amounts, accumulated savings, and target deadlines.
- Automatically calculates monthly required savings with visual progress bars.

---

## 📐 Financial Formulas Reference

| Calculation | Formula | Description |
| :--- | :--- | :--- |
| **Simple Interest (SI)** | $SI = \frac{P \cdot R \cdot T}{100}$ | Standard simple interest calculation |
| **Compound Interest (CI)** | $A = P \left(1 + \frac{r}{n}\right)^{n \cdot T}$ | Compound interest compounded $n$ times per year |
| **EMI** | $EMI = \frac{P \cdot r \cdot (1+r)^n}{(1+r)^n - 1}$ | Monthly payment where $r = \frac{R}{1200}$ |
| **Daily Allowance** | $\frac{\text{Total Budget} - \text{Current Month Spend}}{\text{Days Remaining}}$ | Daily discretionary spending allowance |
| **Run-Rate Forecast** | $\frac{\text{Spend to Date}}{\text{Current Day}} \times \text{Days in Month}$ | Linear month-end spending projection |

---

## 📁 Project Structure

```text
finance-tracker/
├── backend/
│   ├── calculators.py       # Pure finance logic (EMI, SI, CI, payoff simulations)
│   ├── database.py          # SQLite connection and table schemas
│   ├── main.py              # FastAPI application, REST endpoints, and auth
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── app.js               # Frontend controller, Chart.js & Web Speech integration
│   ├── index.html           # Single-page application markup
│   └── style.css            # Custom emerald & gold responsive styles
├── .vscode/
│   ├── extensions.json      # Recommended VS Code extensions
│   └── launch.json          # F5 debug launcher configuration
├── .gitignore               # Ignored environments, databases, and temporary files
├── LICENSE                  # MIT License
├── package.json             # NPM task runner scripts (cross-platform)
├── run.js                   # Node.js runner script
├── sample_transactions.csv  # Sample transactions for testing
├── setup.js                 # Automatic setup and dependency installer
├── test.js                  # Automated test runner
└── README.md                # Project documentation
```

---

## 🚀 Quick Start & Local Setup

### Option 1: Automated with npm (Recommended)
Node.js and Python 3.10+ installed on your system:
```bash
# Install dependencies & configure virtual environment automatically
npm install

# Start the server
npm start
```
The server will start at **http://127.0.0.1:8000**.

### Option 2: Native Python

#### Windows (PowerShell):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

#### macOS / Linux (Terminal):
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open your browser at **http://127.0.0.1:8000**.  
Interactive Swagger API documentation is available at **http://127.0.0.1:8000/docs**.

---

## 🧪 Testing

Run the automated unit test suite covering financial calculators, categorizer, interest, EMI, and payoff logic:

```bash
npm test
```
*Or directly via Python:*
```bash
python -m unittest -v test.js
```

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the frontend single-page web application |
| `GET` | `/api/summary` | Dashboard metrics, forecast, alerts, anomalies, subscriptions |
| `GET` | `/api/transactions` | Lists transactions filtered by `month` |
| `POST` | `/api/transactions` | Records a single income/expense transaction |
| `POST` | `/api/transactions/bulk` | Bulk transaction CSV import |
| `DELETE` | `/api/transactions/{id}` | Deletes a transaction by ID |
| `POST` | `/api/quickadd` | Natural-language parser ("Spent 250 on lunch") |
| `GET` | `/api/budgets` | Lists all monthly category budgets |
| `PUT` | `/api/budgets` | Creates or updates a category budget limit |
| `DELETE` | `/api/budgets/{category}`| Removes a category budget |
| `POST` | `/api/budgets/suggest` | Computes 3-month average cutoff suggestions |
| `GET` | `/api/debts` | Lists recorded loans and cards |
| `POST` | `/api/debts` | Adds a new debt account |
| `DELETE` | `/api/debts/{id}` | Deletes a debt account |
| `GET` | `/api/debts/analysis` | Avalanche vs. Snowball payoff simulation with rollover |
| `GET` | `/api/calc/emi` | Calculates monthly EMI and total interest |
| `GET` | `/api/calc/interest` | Calculates Simple vs. Compound interest |
| `GET` | `/api/goals` | Lists savings goals and monthly required savings |
| `POST` | `/api/goals` | Creates a new financial goal |
| `POST` | `/api/goals/{id}/add` | Deposits savings into a goal |
| `DELETE` | `/api/goals/{id}` | Deletes a financial goal |

---

## ☁️ Deployment Guide (Render)

1. Fork or push this repository to your GitHub account: `https://github.com/Tejareddy-123-la/finance_tracker`.
2. Log into [Render](https://render.com) and click **New +** → **Web Service**.
3. Select the repository and configure:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. *(Optional)* Under **Environment Variables**, add:
   - `APP_PASSWORD`: `your_secure_password` *(Enables HTTP Basic Authentication)*
   - `DB_PATH`: `/var/data/finance.db` *(If utilizing Render Persistent Disks)*
5. Click **Deploy Web Service**.

> [!NOTE]
> Render's free tier uses an ephemeral filesystem that resets when instances sleep or restart. For persistent production data, attach a Render Persistent Disk or configure an external database service such as [Turso (libSQL)](https://turso.tech).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
