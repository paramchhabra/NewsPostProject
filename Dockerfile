FROM python:3.13.3-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Set working directory to root
WORKDIR /

# Copy requirements.txt to root
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files to root
COPY . .

EXPOSE 8501


CMD ["streamlit", "run", "main.py","--server.address=0.0.0.0"]

