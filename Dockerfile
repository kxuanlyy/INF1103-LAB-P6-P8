FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY ai_module/requirements.txt ./ai_module/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ai_module/__init__.py ai_module/ai_manager.py ./ai_module/
COPY data_manager.py io_manager.py logic_manager.py main.py ./
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Singapore
ENV FOODRESCUE_DATA=/app/data/inventory.json
CMD ["python", "main.py"]
