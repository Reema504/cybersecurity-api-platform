# Cybersecurity Tools Management Platform 🚀

A Python-based backend platform using FastAPI, PostgreSQL, and Docker to run cybersecurity tools (Ping, Nmap) via a REST API, featuring DoS protection and results logging.

## 🌟 Features

* Run `ping` commands against any hostname.
* Run fast `nmap` port scans (`-F`) against any hostname.
* All results are automatically saved to a PostgreSQL database with timestamps.
* RESTful API endpoints to view the history of all previous scans (`/history/ping`, `/history/nmap`).
* Includes basic DoS protection using rate limiting.

## 🛠️ Technologies Used

* **Backend:** Python 3.9
* **API Framework:** FastAPI
* **Database:** PostgreSQL
* **Containerization:** Docker & Docker Compose
* **ORM:** SQLAlchemy (for database interaction)
* **Web Server:** Uvicorn

## 🔧 How to Run Locally (Using Docker)

1.  **Prerequisites:** Ensure you have Docker and Docker Compose installed.
2.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Reema504/cybersecurity-api-platform.git](https://github.com/Reema504/cybersecurity-api-platform.git)
    cd cybersecurity-api-platform
    ```
3.  **Build and run the containers:**
    ```bash
    docker-compose up --build
    ```
4.  The application will be accessible at `http://127.0.0.1:8000`.

## 📋 API Endpoints

Here are the available API endpoints:

| Method | Endpoint                    | Description                               |
|--------|-----------------------------|-------------------------------------------|
| GET    | `/ping/{hostname}`          | Runs a ping command against the hostname. |
| GET    | `/scan/nmap/{hostname}`     | Runs an Nmap scan (`-F`) against the hostname.   |
| GET    | `/history/ping`             | Shows the history of all ping results.    |
| GET    | `/history/nmap`             | Shows the history of all Nmap results.    |

**Example Ping Result (`/ping/google.com`):**
```json
{
  "hostname": "google.com",
  "output": "PING google.com (142.250.184.142) 56(84) bytes of data.\n64 bytes from lhr48s23-in-f14.1e100.net (142.250.184.142): icmp_seq=1 ttl=116 time=5.69 ms\n..."
}

## Security Assurance: Command Injection Prevention

The platform is secured against Command Injection vulnerabilities. This critical security measure is achieved by strictly adhering to Python's best practices for running system commands:

1.  **Strict Subprocess Usage:** All system commands (`ping`, `nmap`) are executed using `subprocess.run()`.
2.  **Shell=False (Default):** The `shell=True` parameter is explicitly avoided. This ensures that user inputs (like the hostname) are passed as isolated **arguments** to the command, and are never interpreted as executable shell code.
3.  **Input Segregation:** Inputs are passed as a list of arguments, preventing concatenation of user input with system commands.
