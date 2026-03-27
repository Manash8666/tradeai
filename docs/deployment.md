# Deployment Architecture & Execution Guide

This document outlines the strict execution requirements to securely deploy the **AI Trading Platform** in a production environment (Linux VM or WSL2).

## Host OS Architecture
Because of the heavy reliance on the NautilusTrader core engine (Rust binaries), Deep Learning multi-processing (Scikit-Learn/SHAP), and high-throughput ClickHouse Audit hashing, **native Windows execution via Docker Desktop is unsupported for production volumes.**

### ✅ Supported Operating Systems
1. **Ubuntu 22.04 LTS (or newer)** - *Recommended for AWS EC2 / DigitalOcean Droplets.*
2. **Debian 12**
3. **Windows 11 with WSL2 (Ubuntu)** - *Recommended for local development architecture.*

---

## 🚀 Execution Steps (WSL2 / Linux)

### 1. Pre-requisites
Ensure the host has the latest `docker` and `docker-compose` v2 plugins installed.
```bash
docker --version
docker compose version
```

### 2. Configure Environment Secrets
DO NOT deploy with the `.env.example` payload. You must generate cryptographic hashes for the following critical environment variables in a `.env` file at the root:

```env
# Essential Overrides
JWT_SECRET_KEY=generate_using_openssl_rand_base64_32
WEBHOOK_SECRET=your_tradingview_hmac_secret
BROKER_STATIC_IP=Your_Assigned_ISP_Static_IP  # Required for SEBI compliance
CLICKHOUSE_PASSWORD=secure_ch_password
POSTGRES_PASSWORD=secure_pg_password
```

### 3. Build & Spin-up the Service Mesh
The platform leverages a custom bridge network (`trading-network`) isolating internal telemetry and databases from public egress.

Execute the daemonized spin-up:
```bash
docker compose up -d --build
```

### 4. Verify Telemetry & AI Subsystems
Verify that the `tp-prometheus` container successfully attaches to the `tp-backend` scrape endpoints.
```bash
docker logs tp-prometheus -n 20
```

Verify the Grafana dashboard is serving securely on Port `3000`. Navigate to `http://<your-droplet-ip>:3000`, configure Prometheus as the default Data Source mapping to `http://prometheus:9090` and import the FastAPI latency templates.

---

## ⚠️ Troubleshooting Mismatched Architectures

If running under native Windows natively (`pwsh`) without WSL2 integration, the Docker binding for `tp-clickhouse` and `tp-postgres` will often throw volume persistence errors. Ensure:
1. Docker Desktop -> Settings -> Resources -> WSL Integration is **enabled** for your distro.
2. The project directory is located *inside* the Linux file system (e.g., `\\wsl$\Ubuntu\home\user\Trading Platform`) rather than mounted across the `/mnt/c/` boundary, which causes massive I/O bottlenecks during live Market ticks.
