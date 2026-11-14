# Smart Personal Finance Manager

A full-stack personal finance application with budgeting, debt payoff modeling, and automatic transaction analysis.

## Quick Start (with npm)
```bash
npm install
npm start
```
This automatically configures the Python virtual environment, installs dependencies, and launches the server at `http://127.0.0.1:8000`.

## Quick Start (Direct Python)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```
Open browser at `http://127.0.0.1:8000` (interactive API documentation at `http://127.0.0.1:8000/docs`).

## Deployment (Render)
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: `APP_PASSWORD=your_secure_password`
