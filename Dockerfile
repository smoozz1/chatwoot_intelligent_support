FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS="ignore" \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Устанавливаем только Node.js и npm для localtunnel
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm && \
    npm install -g localtunnel && \
    # Чистим кэш, чтобы уменьшить образ
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.npm /tmp/*

# Копируем зависимости Python
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install "https://download.pytorch.org/whl/cpu/torch-2.9.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl"

# Копируем исходный код приложения
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
