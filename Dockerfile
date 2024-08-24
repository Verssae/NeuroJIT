FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/neurojit-1.0.0-py3-none-any.whl[replication]

RUN curl -L -o checkstyle.jar https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.15.0/checkstyle-10.15.0-all.jar

RUN chmod +x scripts/*.sh

CMD ["/bin/sh"]
