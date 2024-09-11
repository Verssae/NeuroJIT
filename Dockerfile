FROM python:3.12-slim AS build-stage

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean


RUN curl -L -o checkstyle.jar https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.15.0/checkstyle-10.15.0-all.jar

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-jdk \
    git \
    && apt-get clean


RUN pip install neurojit[replication]==1.0.2

COPY --from=build-stage /app /app

RUN chmod +x scripts/*.sh

EXPOSE 8000

CMD ["scripts/reproduce.sh"]