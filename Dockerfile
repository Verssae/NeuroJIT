# 첫 번째 스테이지: 빌드 및 종속성 설치
FROM python:3.12-slim AS build-stage

# 작업 디렉토리 설정
WORKDIR /app

# 모든 파일을 복사 (dist 디렉토리 포함)
COPY . .

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean


# Checkstyle 다운로드
RUN curl -L -o checkstyle.jar https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.15.0/checkstyle-10.15.0-all.jar

# 두 번째 스테이지: 최종 이미지 구축 (실행에 필요한 JDK와 git 포함)
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지 설치 (JDK와 git은 실행 시 필요하므로 포함)
RUN apt-get update && apt-get install -y \
    default-jdk \
    git \
    && apt-get clean


RUN pip install neurojit[replication]

# 첫 번째 스테이지에서 필요한 파일만 복사
COPY --from=build-stage /app /app

# 스크립트 실행 권한 설정
RUN chmod +x scripts/*.sh

# 기본 포트 노출
EXPOSE 8000

# 애플리케이션 실행을 위한 기본 명령 설정
CMD ["scripts/reproduce.sh"]