# Configuration Guide

This guide explains how to configure dynamic file pulling using patterns.

## Overview

The configuration supports two methods for pulling files:

1. **Static Mappings** (`engineering_paths` / `operations_paths`): Manually specify each file
2. **Pattern Matching** (`engineering_patterns` / `operations_patterns`): Automatically discover files using glob patterns

## Pattern-Based Configuration

### Basic Pattern Examples

```json
{
  "engineering_patterns": [
    {
      "source": "docs/*.md",
      "destination": "docs/engineering/",
      "description": "Copy all markdown files from docs/ directory"
    }
  ]
}
```

### Pattern Types

#### 1. Simple File Pattern
Copy all `.md` files from a directory:
```json
{
  "source": "docs/*.md",
  "destination": "docs/engineering/"
}
```

#### 2. Recursive Pattern (All Subdirectories)
Copy all `.md` files recursively:
```json
{
  "source": "docs/**/*.md",
  "destination": "docs/engineering/",
  "recursive": true,
  "description": "Copy all markdown files recursively"
}
```

#### 3. Directory Pattern
Copy entire directory structure:
```json
{
  "source": "docs/guides/",
  "destination": "docs/engineering/guides/",
  "description": "Copy entire guides directory"
}
```

#### 4. Multiple Patterns
You can use multiple patterns for different directories:
```json
{
  "engineering_patterns": [
    {
      "source": "docs/api/*.md",
      "destination": "docs/engineering/api/"
    },
    {
      "source": "docs/guides/**/*.md",
      "destination": "docs/engineering/guides/",
      "recursive": true
    }
  ]
}
```

## Configuration Options

### Pattern Configuration Fields

- **`source`** (required): Glob pattern or file path to match
  - Examples: `docs/*.md`, `docs/**/*.md`, `docs/guides/`
  - Use `**` for recursive matching
  - Use `*` for single-level wildcard

- **`destination`** (required): Destination directory or file path
  - If ends with `/`: Treated as directory, preserves file structure
  - If file path: Specific destination file

- **`recursive`** (optional): Boolean, default `false`
  - If `true`, searches subdirectories recursively
  - Automatically `true` if pattern contains `**`

- **`description`** (optional): Human-readable description for logging

### Global Options

- **`exclude_patterns`**: Array of patterns to exclude
  - Applied to all file operations
  - Examples: `["*.tmp", "*.bak", ".*", "README.md"]`

## Examples

### Example 1: Copy All Documentation Files

```json
{
  "engineering_patterns": [
    {
      "source": "docs/**/*.md",
      "destination": "docs/engineering/",
      "description": "Copy all markdown files recursively"
    }
  ],
  "exclude_patterns": ["*.draft.md", "*.old.md"]
}
```

This will:
- Copy all `.md` files from `docs/` and all subdirectories
- Preserve directory structure in `docs/engineering/`
- Exclude any files matching exclusion patterns

### Example 2: Copy Specific Directories

```json
{
  "engineering_patterns": [
    {
      "source": "docs/api/**/*.md",
      "destination": "docs/engineering/api/"
    },
    {
      "source": "docs/guides/**/*.md",
      "destination": "docs/engineering/guides/"
    }
  ]
}
```

### Example 3: Mix Static and Dynamic

```json
{
  "engineering_paths": {
    "docs/important.md": "docs/engineering/important.md"
  },
  "engineering_patterns": [
    {
      "source": "docs/api/*.md",
      "destination": "docs/engineering/api/"
    }
  ]
}
```

This allows you to:
- Use static mappings for specific important files
- Use patterns for directories that change frequently

## Best Practices

1. **Use patterns for directories that grow**: If you frequently add new files, use patterns
2. **Use static mappings for critical files**: Ensure important files are always included
3. **Use exclusion patterns**: Filter out draft, temporary, or private files
4. **Be specific with patterns**: Avoid overly broad patterns that might copy unwanted files
5. **Test locally**: Always test pattern matching locally before deploying

## Pattern Syntax Reference

| Pattern | Matches |
|---------|---------|
| `*.md` | All `.md` files in a directory |
| `**/*.md` | All `.md` files recursively |
| `docs/*.md` | All `.md` files in `docs/` |
| `docs/**/*.md` | All `.md` files in `docs/` and subdirectories |
| `docs/api/*.md` | All `.md` files in `docs/api/` |
| `*guide*.md` | Files with "guide" in the name |
| `docs/guides/` | Entire directory (if it's a directory) |

## Troubleshooting

### No files matched
- Check the `source` path exists in the repository
- Verify the pattern syntax is correct
- Check if files are excluded by `exclude_patterns`

### Files in wrong location
- Verify `destination` path ends with `/` if you want to preserve structure
- Check relative path calculations

### Too many files copied
- Add more specific patterns
- Use `exclude_patterns` to filter unwanted files
- Be more specific with pattern matching

## Migration from Static to Dynamic

To migrate from static mappings to patterns:

1. Identify common directory structure
2. Create a pattern that matches your files
3. Test the pattern locally
4. Replace static mappings with patterns
5. Keep critical files in static mappings if needed

Example migration:

**Before (Static):**
```json
{
  "engineering_paths": {
    "docs/api/v1.md": "docs/engineering/api/v1.md",
    "docs/api/v2.md": "docs/engineering/api/v2.md",
    "docs/api/v3.md": "docs/engineering/api/v3.md"
  }
}
```

**After (Pattern):**
```json
{
  "engineering_patterns": [
    {
      "source": "docs/api/*.md",
      "destination": "docs/engineering/api/"
    }
  ]
}
```

Now any new files added to `docs/api/` will be automatically included!

