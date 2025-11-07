FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory at build time
RUN mkdir -p /app/logs

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]