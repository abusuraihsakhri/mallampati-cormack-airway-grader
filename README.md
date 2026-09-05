# Mallampati Cormack Airway Grader

> **Domain:** Diagnostic Radiology & Medical Imaging AI
> **Reference Guidelines & Standards:** `American College of Radiology (ACR) RADS & Fleischner Society`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Airway Assessment (Mallampati & Cormack-Lehane)
Combines modified Mallampati, thyromental distance, and Cormack-Lehane grade for difficult intubation risk.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`**: Core domain algorithm for airway grading with weighted scoring.
- **`process_single()`** — Evaluates a single case with provided parameters.
- **`process_batch()`** — Processes CSV files with multiple records.
- **`main()`** — CLI entry point for single and batch operations.

### 🏗️ Enterprise Architecture

- **Multi-Agent Supervisor System**: Coordinates specialized workers for comprehensive evaluation.
- **PHI Outbound Guard**: Prevents protected health information from leaving the system.
- **HMAC-SHA256 Audit Trail**: Tamper-evident cryptographic logging of all operations.
- **FastAPI REST API**: OpenAPI 3.1 compatible REST endpoints.
- **Prometheus Metrics**: Operational telemetry export.

---

## 📐 Mathematical Formulation & Logic

The core algorithm computes a weighted score from input parameters:

```text
score = v1 + v2 * (1/2) + v3 * (1/3) + ...
```

Classification tiers:
- **Low / Standard** (score < 10.0): Standard monitoring
- **Moderate / Intermediate** (10.0 ≤ score < 25.0): Close observation
- **High / Severe** (score ≥ 25.0): Urgent clinical intervention

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/mallampati-cormack-airway-grader.git
cd mallampati-cormack-airway-grader

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set audit key (required for production)
export AUDIT_SECRET_KEY="your-secure-audit-key-min-16-chars"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python airway_grader.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python airway_grader.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI with Audit Trail
```bash
# Set audit key
export AUDIT_SECRET_KEY="your-secure-audit-key"

# Run audit
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail
python cli.py verify-audit

# Start API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--v1`: Primary parameter (Mallampati score)
- `--v2`: Secondary parameter (thyromental distance)
- `--v3`: Tertiary parameter (Cormack-Lehane grade)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement (Mallampati) | Required |
| `v2` | Secondary measurement (thyromental distance) | Required |
| `v3` | Tertiary measurement (Cormack-Lehane) | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **Input Validation:** Bounds checking and sanitization for all numeric inputs.
* **Path Traversal Protection:** File path validation prevents directory traversal attacks.
* **Configurable Audit Key:** Secure key management via environment variable.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Set test audit key
export AUDIT_SECRET_KEY="test-audit-key-for-testing-only"

# Run all tests
pytest -v

# Run specific test files
pytest test_airway_grader.py -v
pytest tests/ -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t mallampati-cormack-airway-grader .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" mallampati-cormack-airway-grader
```

---

## 📁 Project Structure

```
mallampati-cormack-airway-grader/
├── airway_grader.py          # Core grading algorithm
├── cli.py                    # Enterprise CLI interface
├── simulator.py              # Load testing simulator
├── enrichment.py             # Feature enrichment modules
├── sample.csv                # Sample input data
├── test_airway_grader.py     # Core algorithm tests
├── agents/
│   ├── __init__.py           # Package initialization
│   ├── api.py                # FastAPI REST server
│   ├── base.py               # Security, PHI guard, audit trail
│   ├── models.py             # Pydantic data models
│   ├── supervisor.py         # Multi-agent orchestrator
│   ├── workers.py            # Specialized evaluation workers
│   ├── llm_factory.py        # LLM integration factory
│   ├── learning.py           # Bayesian calibration engine
│   ├── metrics.py            # Prometheus metrics collector
│   └── streamer.py           # WebSocket telemetry broadcaster
├── tests/
│   ├── test_mallampati_cormack_airway_grader.py
│   └── test_enrichment.py
├── web/
│   └── index.html            # Operations console UI
├── Dockerfile
├── docker-compose.yml
└── LICENSE
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
