FROM python:3.7-slim
RUN mkdir /app
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends\
    build-essential\
    python3-dev\
    python3-pip\
    python3-setuptools\
    python3-wheel\
    python3-cffi\
    libcairo2\
    libpango-1.0-0\
    libpangocairo-1.0-0\
    libgdk-pixbuf2.0-0\
    libffi-dev\
    shared-mime-info && \
    apt-get clean
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]