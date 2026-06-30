FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by scikit-learn at import time.
# unset proxy envs so apt goes direct (Debian repos don't need proxy in CN via DNS).
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy all_proxy ALL_PROXY && \
    apt-get update -qq && apt-get install -y -qq --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Build-time proxy for pip (passed via --build-arg). Defaults to empty so
# production CI builds without proxy still work.
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""

# Copy & install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy project source — only what the app needs at runtime
COPY projects/ml_playground/ projects/ml_playground/
COPY models/ models/
COPY data/ data/

EXPOSE 8000

CMD ["uvicorn", "projects.ml_playground.app:app", "--host", "0.0.0.0", "--port", "8000"]
