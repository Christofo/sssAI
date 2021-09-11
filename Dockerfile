FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
RUN apt-get update \
      && apt-get upgrade -y \
      && rm -rf /var/lib/apt/lists/*

ARG TZ
ENV TZ=${TZ:-America/New_York}
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

RUN pip install requests loguru pillow

COPY ./app /app
COPY run.py /run.py
CMD ["python", "/run.py"]
