# UnstructuredIO Local Deployment Guide

## Overview

This guide documents how to deploy UnstructuredIO locally for PDF and Excel document processing. UnstructuredIO provides a high-performance API for parsing various document formats into structured data.

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker installed (Windows: Docker Desktop)
- 4GB+ RAM available
- 10GB+ disk space

### Step 1: Pull the Docker Image

```bash
# Pull the latest Unstructured API server
docker pull unstructured-io/unstructured-api:latest

# Or use the full version with all dependencies
docker pull unstructured-io/unstructured-api:latest-gpu  # For GPU support
```

### Step 2: Run the Container

```bash
# Basic run (CPU only)
docker run -p 8000:8000 \
  -v /path/to/local/data:/app/data \
  unstructured-io/unstructured-api:latest

# With GPU support (requires NVIDIA Docker)
docker run -p 8000:8000 \
  --gpus all \
  -v /path/to/local/data:/app/data \
  unstructured-io/unstructured-api:latest-gpu

# Production deployment with restart policy
docker run -d \
  --name unstructured-api \
  -p 8000:8000 \
  -v /path/to/local/data:/app/data \
  --restart unless-stopped \
  unstructured-io/unstructured-api:latest
```

### Step 3: Verify Installation

```bash
# Test the API
curl http://localhost:8000/healthcheck

# Expected response:
# {"status": "OK"}
```

## Option 2: Python Installation (Development)

### Prerequisites
- Python 3.9+
- pip or conda

### Step 1: Install from Source

```bash
# Clone the repository
git clone https://github.com/Unstructured-IO/unstructured.git
cd unstructured

# Install in development mode
pip install -e ".[all-docs]"

# Or install specific dependencies
pip install unstructured pdf2image pytesseract
```

### Step 2: Run the API Server

```bash
# Start the API server
python -m unstructured_api.main --host 0.0.0.0 --port 8000

# With custom settings
python -m unstructured_api.main \
  --host 0.0.0.0 \
  --port 8000 \
  --model-hub huggingface \
  --table-extraction-mode fast
```

## Option 3: Docker Compose (Production)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  unstructured-api:
    image: unstructured-io/unstructured-api:latest
    container_name: unstructured-api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - UNSTRUCTURED_PARALLEL_THREADS=4
      - UNSTRUCTURED_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Start the service:

```bash
docker-compose up -d
docker-compose logs -f unstructured-api
```

## API Usage Examples

### Basic Document Parsing

```bash
# Parse a PDF
curl -X POST "http://localhost:8000/general/v0.0.0/general" \
  -H "accept: application/json" \
  -F "files=@document.pdf" \
  -F "strategy=auto"

# Parse an Excel file
curl -X POST "http://localhost:8000/general/v0.0.0/general" \
  -H "accept: application/json" \
  -F "files=@spreadsheet.xlsx" \
  -F "strategy=fast"
```

### Python Client

```python
from unstructured.partition.auto import partition
from unstructured.staging.base import convert_to_dict

# Parse document
elements = partition(
    filename="document.pdf",
    strategy="auto",  # auto, fast, hi_res, ocr_only
    include_page_breaks=True
)

# Convert to structured format
data = convert_to_dict(elements)

# Print extracted content
for element in data:
    print(f"{element['type']}: {element['text']}")
```

## Document Processing Strategies

| Strategy | Speed | Quality | Use Case |
|----------|-------|---------|----------|
| `fast` | Fastest | Good | Simple documents, text-based PDFs |
| `auto` | Medium | Better | Mixed content, default choice |
| `hi_res` | Slowest | Best | Complex layouts, tables, images |
| `ocr_only` | Slow | Best | Scanned documents, images |

## Supported Document Types

- **PDF**: .pdf
- **Word**: .docx, .doc
- **Excel**: .xlsx, .xls, .csv
- **PowerPoint**: .pptx, .ppt
- **Text**: .txt, .md, .html
- **Images**: .png, .jpg, .tiff (with OCR)
- **Email**: .eml, .msg
- **Archive**: .zip (auto-extracts)

## Performance Optimization

### For High Volume Processing

```bash
# Increase parallel threads
docker run -e UNSTRUCTURED_PARALLEL_THREADS=8 ...

# Increase memory limit
docker run -m 8g ...

# Use GPU for faster OCR
docker run --gpus all ...
```

### Caching Configuration

```bash
# Enable Redis caching (optional)
docker run -e REDIS_URL=redis://localhost:6379 ...
```

## Troubleshooting

### Common Issues

#### 1. Memory Errors
```bash
# Increase container memory
docker run -m 8g ...
```

#### 2. Tesseract OCR Not Found
```bash
# Install Tesseract separately (Linux)
sudo apt-get install tesseract-ocr

# On Windows, add to PATH or use:
docker run -v /path/to/tesseract:/usr/bin/tesseract ...
```

#### 3. Slow Processing
```bash
# Use faster strategy
strategy=fast

# Increase threads
UNSTRUCTURED_PARALLEL_THREADS=8
```

### Health Check Commands

```bash
# Check container status
docker ps | grep unstructured

# Check logs
docker logs unstructured-api

# Test API endpoint
curl http://localhost:8000/healthcheck

# Test document parsing
curl -X POST "http://localhost:8000/general/v0.0.0/general" \
  -F "files=@test.pdf" \
  -F "strategy=fast"
```

## Integration with Paper Writer System

### Update Configuration

```yaml
# config/config.yaml
document_processing:
  provider: "unstructured"
  api_url: "http://localhost:8000"
  strategy: "auto"  # auto, fast, hi_res, ocr_only
  timeout: 300  # seconds
```

### Python Integration

```python
from src.document_processor import UnstructuredDocumentProcessor

# Initialize
processor = UnstructuredDocumentProcessor(
    api_url="http://localhost:8000",
    strategy="auto"
)

# Parse PDF
elements = processor.parse_pdf("paper.pdf")

# Extract text by section
sections = processor.extract_sections(elements)
```

## Monitoring and Logging

### Enable Detailed Logging

```bash
# Set log level
docker run -e UNSTRUCTURED_LOG_LEVEL=DEBUG ...
```

### Metrics Endpoint

```bash
# Prometheus metrics (if enabled)
curl http://localhost:8000/metrics
```

## Security Considerations

### Production Deployment

```bash
# Disable CORS in production
docker run -e ALLOW_ORIGINS=https://your-domain.com ...

# Add authentication
# (Configure reverse proxy with auth)
```

### Rate Limiting

```bash
# Configure rate limits
docker run -e MAX_REQUESTS_PER_MINUTE=100 ...
```

## Backup and Recovery

### Data Persistence

```bash
# Volumes for processed data
docker run -v /path/to/output:/app/output ...
```

### Container Backup

```bash
# Backup container configuration
docker commit unstructured-api backup-$(date +%Y%m%d)
```
