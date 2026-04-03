FROM python:3.12-slim

RUN groupadd -r pca && useradd -r -g pca -d /app -s /sbin/nologin pca

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R pca:pca /app

USER pca

EXPOSE 5000

CMD ["python", "run.py"]
