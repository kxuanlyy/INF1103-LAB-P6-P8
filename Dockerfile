FROM python:3.12-slim AS base

WORKDIR /app

# System libraries the PySide6 (Qt) GUI needs to import and start inside a slim image
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-dejavu-core libgl1 libegl1 libglib2.0-0 libfontconfig1 libdbus-1-3 libxkbcommon0 libxkbcommon-x11-0 \
        libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
        libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first so this layer is cached until a requirements file changes
COPY requirements.txt .
COPY ai_module/requirements.txt ./ai_module/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r ai_module/requirements.txt

# Application code and seed data; .dockerignore excludes local generated results.
COPY main.py ./
COPY ai_module/ ./ai_module/
COPY data_manager/ ./data_manager/
COPY io_manager/ ./io_manager/
COPY logic_manager/ ./logic_manager/

ENV PYTHONUNBUFFERED=1
ENV QT_XCB_GL_INTEGRATION=none
ENV LIBGL_ALWAYS_SOFTWARE=1

# --- Target 1: Interactive Application ---
# Terminal:  docker run --rm -it --env-file apikey.env foodrescue-ai-oop
# GUI:       docker run --rm -it --env-file apikey.env -e DISPLAY=host.docker.internal:0.0 foodrescue-ai-oop --gui

FROM base AS app
ENTRYPOINT ["python", "main.py"]
CMD []

# --- Target 2: Automated Unit Tests ---
FROM base AS test
COPY tests/ ./tests/
ENV QT_QPA_PLATFORM=offscreen
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
