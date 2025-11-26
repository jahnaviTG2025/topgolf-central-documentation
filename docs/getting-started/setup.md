# Setup Guide

This guide will help you set up the documentation repository for local development.

## Prerequisites

- Python 3.8 or higher
- Git
- Access to Engineering and Operations repositories (for pulling content)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/central-documentation.git
cd central-documentation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure repository URLs in `scripts/config.json`:
```json
{
  "engineering_repo": "https://github.com/your-org/engineering-repo.git",
  "engineering_branch": "main",
  "engineering_paths": [
    "docs/api.md",
    "docs/architecture.md"
  ],
  "operations_repo": "https://github.com/your-org/operations-repo.git",
  "operations_branch": "main",
  "operations_paths": [
    "docs/deployment.md",
    "docs/monitoring.md"
  ]
}
```

4. Pull external content:
```bash
python scripts/pull_content.py
```

5. Preview the documentation:
```bash
mkdocs serve
```

The documentation will be available at `http://127.0.0.1:8000`

## Building for Production

To build the documentation site:

```bash
mkdocs build
```

The built site will be in the `site/` directory.

