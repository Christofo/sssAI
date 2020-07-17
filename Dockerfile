FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY ./app /app
COPY run.py /run.py
CMD ["python", "/run.py"]
RUN pip install requests loguru