# OrderFlow

This is the Inital workflow, this will change as the projects grow.

Below contain the workflow and actual approach to solve this Problem.

<img width="2470" height="1306" alt="image" src="https://github.com/user-attachments/assets/9e7730a8-e52f-4937-99ee-389d992c3db0" />

**Gateway Exchange → Data Ingestion Service**

- The exchange (e.g., Deribit) provides market data.

- The ingestion service connects to the exchange, subscribes to data, and normalizes it.

**Data Distribution**

- Data is pushed into NATS ( JetStream for durable streams & replay).

**Consumers**

- Services and CLIs (Frontends) subscribe to NATS subjects to get live data.

- This allows scaling multiple independent consumers without coupling to ingestion.

  ##  Initial Approach / Todo

- [ ] Build a **Python CLI**
  - [ ] Start a **basic ingestion service** (connect to Deribit, fetch orderbook stream)
  - [ ] Start and configure **NATS JetStream**
  - [ ] Provide a **CLI for consuming data** (subscribe and display)


<img width="970" height="406" alt="image" src="https://github.com/user-attachments/assets/9f9f4074-db38-49ee-bf94-27416b585a8e" />


# Installation

This project is managed by uv. Hence these are some steps to follow for setup.

```bash
# Create a virtual env
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# UV install
uv sync

# CLI Working
task click
```

```bash
# To run service cli
task click service
  
```


## Docker Stack

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volume (ideal for removing cache)
docker-compose down -v
```
