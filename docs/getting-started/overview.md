# Getting Started

This guide will help you understand how to use and contribute to the central documentation repository.

## Documentation Structure

The central documentation repository is organized into several sections:

### Engineering Section
Contains technical documentation pulled from the Engineering repository:
- API documentation
- Architecture diagrams and guides
- Development guidelines
- Technical specifications

### Operations Section
Contains operational documentation pulled from the Operations repository:
- Deployment procedures
- Monitoring and alerting guides
- Troubleshooting documentation
- Infrastructure guides

### AsyncAPI Section
Contains AsyncAPI specifications and documentation for event-driven architectures.

## How Content is Pulled

Content from external repositories is pulled using automated scripts during the documentation build process. The scripts:

1. Clone or update content from the Engineering repository
2. Clone or update content from the Operations repository
3. Copy specific pages/files to the documentation structure
4. Build the documentation site

## Building Locally

See the [Setup Guide](setup.md) for instructions on building the documentation locally.

