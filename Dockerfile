# ── 1. Base image ──────────────────────────────────────────────────────
FROM python:3.10-slim

# ── 2. Working directory inside the container ──────────────────────────
WORKDIR /app

# ── 3. Install dependencies first (cached layer unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 4. Copy the rest of the source code ───────────────────────────────
COPY . .

# ── 5. Expose the port uvicorn will listen on ─────────────────────────
EXPOSE 8000

# ── 6. Start the app (0.0.0.0 so it's reachable outside the container) ─
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
