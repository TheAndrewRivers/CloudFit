FROM python:3
COPY pperformancemonitor.py /app/performancemonitor.py
COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev
RUN pip install -r requirements.txt

CMD ["python", "/app/performancemonitor.py"]
