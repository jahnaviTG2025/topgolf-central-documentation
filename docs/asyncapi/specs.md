# AsyncAPI Specifications

This page contains AsyncAPI specifications for our event-driven systems.

## Available Specifications

### Example Specification

You can add your AsyncAPI specification files here. These can be:

- YAML files with `.yaml` or `.yml` extension
- JSON files with `.json` extension

## Integration with MkDocs

AsyncAPI specifications can be rendered in MkDocs using plugins or by converting them to Markdown.

### Option 1: Using AsyncAPI Generator

Convert AsyncAPI specs to HTML/Markdown using the AsyncAPI generator:

```bash
ag asyncapi.yaml markdown -o docs/asyncapi/generated/
```

### Option 2: Direct YAML/JSON Display

You can embed AsyncAPI specifications directly in Markdown using code blocks:

```yaml
asyncapi: '2.6.0'
info:
  title: Example API
  version: '1.0.0'
servers:
  production:
    url: api.example.com
    protocol: kafka
```

## Adding New Specifications

1. Add your AsyncAPI specification file to the `docs/asyncapi/` directory
2. Update this page to include a link to the specification
3. Optionally, generate documentation using AsyncAPI tools

---

*For more information, visit [AsyncAPI Documentation](https://www.asyncapi.com/docs)*

