FROM python:3.11.7

RUN pip install --upgrade pip

# install torch
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir lightning fastapi uvicorn

WORKDIR /app

COPY model.py /app/model.py
COPY predict.py /app/predict.py
COPY schema.py /app/schema.py

EXPOSE 3000

CMD uvicorn predict:app --host 0.0.0.0 --port 3000 --workers 2

