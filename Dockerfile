FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
COPY ai_module/requirements.txt ./ai_module/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ai_module/__init__.py ai_module/ai_manager.py ./ai_module/
COPY main.py io_manager.py data_manager.py logic_manager.py test_logic_manager.py ./
COPY food_inventory.csv accepted_recipe.json recipes.json ./

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Singapore

# --- Target 1: Interactive Application ---
FROM base AS app
CMD ["python", "main.py"]

# --- Target 2: Automated Unit Tests ---
FROM base AS test
CMD ["python", "-m", "unittest", "test_logic_manager.py", "-v"]