# MultiFramework Real-Time Object Detection with WebRTC

This project implements a real-time object detection system using WebRTC for peer-to-peer communication between devices and a server. It leverages the power of YOLO (You Only Look Once) for object detection, processing video frames sent from the client, and returns bounding box coordinates, class IDs, class names, and confidence values. The server can be run using FastAPI, aiohttp, or Flask, offering flexibility in the choice of web framework, while the client-side uses JavaScript to render the detection results on a canvas in real-time.


## Project Structure

    Project/
    │
    ├── app/
    │   ├── static/
    │   │   ├── css/
    │   │   │   └── style.css
    │   │   ├── images/
    │   │   └── js/
    │   │       └── app.js
    │   ├── templates/
    │   │   └── index.html
    │   ├── logs/
    │   │   └── app.log
    │   ├── aiohttp_web.py
    │   ├── config.py
    │   ├── decorator.py
    │   ├── detector.py
    │   ├── fastapiuweb.py
    │   ├── flask_web.py
    │   ├── logs.py
    │   ├── webapp.py
    │   └── yolov8n.pt
    │
    ├── configs/
    │   ├── local.toml
    │   └── prod.toml
    │
    ├── .gitignore
    ├── cert.pem
    ├── key.pem
    ├── main.py
    ├── README.md
    └── requirements.txt

# Installation Instructions

## Docker and Docker Compose Installation

**1. Install Docker and Docker Compose:**

Ensure Docker and Docker Compose are installed on your system. You can follow the Docker installation guide and the Docker Compose installation guide.

**2.Build Docker Image:**
In your project root directory, build the Docker image using:
```bash
docker compose build --build-arg CUDA_VERSION=your_cuda_version .

```

**3. Start Containers with Docker Compose:**
Start your application using Docker Compose by running:

```bash
docker-compose up
```

This command will start all necessary containers as defined in the docker-compose.yml file.

## Docker Compose File

Here is the updated `docker-compose.yml` file:

```bash
services:
  yolo:
    build: 
        context: .
        dockerfile: Dockerfile
        args:
          CUDA_VERSION: ${CUDA_VERSION} 
    ports:
      - "8000:8000" 
    volumes:
      - /logs:/app/logs  
    network_mode: "host"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    runtime: nvidia
```


## Conda Environment Installation
 
**1. Create Conda Environment:**


```bash
    conda create --name <my-env> python=3.x 
```
* Note: Python 3.8 is recommended for better compatibility with dependencies. You can specify it as follows if needed:

**2. Activate the Conda Environment:**

```bash
    conda activate <my-env>
```

## Install Required Packages:

Make sure you have `requirements.txt` in your project root directory and make sure you are in project root `username@username:~/Project$` like this (This is for Ubuntu)

```bash
    pip install -r requirement.txt
```

## CUDA Installation and Usage

_This project requires the use of CUDA on NVIDIA GPUs for optimal performance. Follow the steps below to install CUDA:_

**1. Check System Requirements:**
- Ensure that you have an NVIDIA GPU
- Check that your system supports the recommended drivers

**2. Install NVIDIA GPU Drivers:**
- Download and install the latest NVIDIA drivers from the [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)

**3.Download and Install CUDA Toolkit:**
- Download the appropriate CUDA version for your operating system from the [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

- You can check this blog for Installation [NVIDIA CUDA Toolkit Installation](https://www.cherryservers.com/blog/install-cuda-ubuntu)

> Note: You Have To Check First What Version of CUDA Suitable for Your System 

You can check with this: `nvidi-smi`


**4. Set Up Environment Variables**
- After installing CUDA, add directories to your system Path
    - **Windows:** Edit environment variables from system properties.
    - **Linux/macOS:** Add the following lines to your `source ~/.bashrc` at the end of line 
    ```
    export PATH=/usr/local/cuda/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
    ```
**5. Verify the Installation:**
- Run the following command in the terminal to check the CUDA version:
`nvcc --version`

*Once the CUDA installation is complete, our project will automatically utilize the GPU. If you encounter any issues, please refer to NVIDIA's official documentation*


# How to run code 

## Before Run You Need SSL KEY and CERTIFICATE

**You can use this line of code**
``` 
    First make sure you are in the project directory
```

```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout server_key.pem -out server_cert.pem -days 365 -subj "/C=TR/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

```

## Running `main.py`
to start the application using `main.py`, open a terminal go to project directory and run:


```bash
    python main.py
```
this will execute the main entry point of the application

## Running Modules Directly
If you want to run specific modules directly, navigate to the `app` directory and run the desired module 

**1.Navigate to the `app` directory:**

```bash
    cd app
```

**2.Run FastAPI Application:**

```bash
    python fastapiweb.py
```

**3.Run Flask Application:**

```bash
    python flaskweb.py
```

**4.Run AIOHTTP Application:**

```bash
    python aiohttpweb.py
```

# Configuration
The application uses TOML files for configuration. You can choose between `local.toml` and `prod.toml` when running the application.

To specify a configuration file:
```bash
python main.py --env prod.toml
```

