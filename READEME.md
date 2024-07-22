# Project Idea

This project offers developers a flexible web server application. Key features include:

1. Support for FastAPI and Flask
2. Easy configuration
3. Static file and template management
4. Advanced logging
5. Settings for different environments (local, production)
6. Command-line control

The goal is to provide a quick and adaptable infrastructure for web applications.

# Installation Instructions

## Setting Up the Conda Environment

### Conda Environment Installation

### 1. Create Conda Environment:


```bash
    conda create --name <my-env> python=3.x 
```
* Note: Python 3.8 is recommended for better compatibility with dependencies. You can specify it as follows if needed:

### 2. Activate the Conda Environment:

```bash
    conda activate <my-env>
```

### Install Required Packages:

Make sure you have `requirements.txt` in your project root directory

```bash
    pip install -r requirement.txt
```

## Alternative Using `requirements.txt` Directly

If you prefer not to use Conda, you can install the necessary packages using `pip` in a standard Python environment.

### 1.Install Required Packages:

```bash
    pip install -r requirements.txt
```

## Project Structure

    project_root/
    │
    ├── app/
    │   ├── static/
    │   │   ├── css/
    │   │   ├── images/
    │   │   └── js/
    │   ├── templates/
    │   │   └── index.html
    │   ├── config.py
    │   ├── fastapiapp.py
    │   ├── flaskapp.py
    │   ├── logs.py
    │   └── webapp.py
    │
    ├── configs/
    │   ├── init.py
    │   ├── local.toml
    │   └── prod.toml
    │
    ├── logs/
    │   └── app.log
    │
    ├── init.py
    ├── main.py
    ├── README.md
    └── requirements.txt


# How to run code 

## Running `main.py`
to start the application using `main.py`, open a terminal and run:


```bash
    python main.py
```
this will execute the main entry point of the application

## Running Modules Directly
If you want to run specific modules directly, navigate to the `app` directory and run the desired module 

### 1.Navigate to the `app` directory:

```bash
    cd app
```

### 2.Run FastAPI Application:

```bash
    python fastapiweb.py
```

### 3.Run Flask Application:

```bash
    python flaskweb.py
```

# Configuration
The application uses TOML files for configuration. You can choose between `local.toml` and `prod.toml` when running the application.

To specify a configuration file:
```bash
python main.py --env prod.toml
```