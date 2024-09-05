ARG CUDA_VERSION="12.4.0"
FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu20.04

# Gerekli bağımlılıkların yüklenmesi ve saat diliminin ayarlanması
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive TZ=Europe/Istanbul apt-get install -y \
    python3.8 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tzdata && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python paketlerinin yüklenmesi
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# SSL sertifikalarının oluşturulması
RUN openssl req -x509 -newkey rsa:4096 -nodes -keyout server_key.pem -out server_cert.pem -days 365 -subj "/C=TR/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

# Uygulama dosyalarını kopyala
COPY . /app
COPY main.py /app/

# Uygulamayı başlat
CMD ["python3", "main.py"]

