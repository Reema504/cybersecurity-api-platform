# Architectural Design Document: Cybersecurity API Platform

## 1. System Overview and Goals

The platform is designed as a **Micro-service Oriented Monolith** initially, with clear component separation to facilitate future horizontal scaling into true microservices.

**Core Goals:**
1.  **Non-Blocking API:** Ensure the API remains highly responsive by offloading time-consuming operations (Ping, Nmap) to background workers.
2.  **Data Integrity:** Use a robust, ACID-compliant database for result logging.
3.  **Security Focus:** Prioritize safe command execution and API protection.

## 2. Component Architecture

The system is composed of four primary, containerized components:

| Component | Technology | Role | Design Rationale |
| :--- | :--- | :--- | :--- |
| **Web Service (API)** | FastAPI (Python) | Handles all HTTP requests, authentication (placeholder), rate limiting, and task queuing. | Chosen for its performance (ASGI) and rapid development speed. |
| **Worker Queue (Broker)** | Redis | Acts as the message broker for the Celery task queue. | Lightweight, highly performant, and reliable for high-volume task dispatch. |
| **Background Workers** | Celery | Executes long-running, CPU/I/O-bound system commands (`ping`, `nmap`). | Decouples the API from the command execution, ensuring the API never blocks. Allows for easy scaling by adding more worker instances. |
| **Database** | PostgreSQL | Stores command history, results, and logging data. | Selected for its strong data integrity (ACID compliance), excellent performance with structured and unstructured data (JSON support), and maturity in production environments. |

## 3. Design Decisions & Scalability

### A. Asynchronous Task Processing (Celery)

* **Decision:** All system operations (`/ping`, `/scan`) are processed via a dedicated **Celery Queue**.
* **Impact:** The API endpoint immediately returns a `task_id` (HTTP 200) instead of waiting for the command to finish. This transforms a **synchronous, blocking** operation into an **asynchronous, non-blocking** one.
* **Scalability:** To handle increased load (e.g., millions of scans), we can scale horizontally simply by deploying more **Celery Worker containers** without touching the main API or database.

### B. Security and Protection Layers

* **Command Injection:** Prevented by using `subprocess.run(shell=False)` (documented in README).
* **Rate Limiting:** A basic **DoS protection Middleware** is implemented in `main.py` using a time-based window to track and block excessive requests from a single IP, serving as the first line of defense against abuse.

### C. Future Enhancements (Scalability Hooks)

* **Caching Layer:** Introduce a Redis Caching layer between the API and PostgreSQL for frequently accessed data (e.g., recent scan history) to reduce database load.
* **Metrics & Monitoring:** Implement the ELK Stack (Elasticsearch, Logstash, Kibana) or Prometheus/Grafana for comprehensive logging, monitoring, and performance tracking across all containers (API, Workers, DB).
