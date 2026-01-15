# Central Documentation Repository

A centralized documentation repository that dynamically pulls content from Engineering and Operations repositories and publishes it as a beautiful, searchable website using MkDocs.

## 🎯 Overview

This repository serves as the central hub for all documentation, combining content from:

- **Engineering Repository**: Technical documentation, API references, and architecture guides
- **Operations Repository**: Deployment guides, monitoring documentation, and operational procedures

The documentation is automatically built and published using [MkDocs](https://www.mkdocs.org/) with the Material theme, providing a modern, responsive documentation website.

## ✨ Features

- **Multi-Repository Content**: Automatically pulls specific pages from Engineering and Operations repos
- **Dynamic File Discovery**: Pattern-based file matching automatically includes new files without config changes
- **Automated Builds**: GitHub Actions workflow builds and deploys documentation on every push
- **Daily Updates**: Scheduled workflow pulls latest content from external repositories daily
- **AsyncAPI Support**: Ready for AsyncAPI specification documentation
- **Search Functionality**: Built-in search powered by MkDocs Material theme
- **Responsive Design**: Mobile-friendly documentation site

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.8 or higher installed
- ✅ Git installed and configured
- ✅ GitHub account
- ✅ Access to Engineering and Operations repositories (if private, configure authentication)

## 🚀 Setup Instructions

### Step 1: Clone and Configure Repository

1. **Clone this repository** (or copy files to your new repository):
   ```bash
   git clone <your-repo-url>
   cd central-documentation
   ```

2. **Update `scripts/config.json`** with your repository information:

   Replace `your-org` with your GitHub organization/username:

   ```json
   {
     "engineering_repo": "https://github.com/YOUR-ORG/engineering-repo.git",
     "engineering_branch": "main",
     "operations_repo": "https://github.com/YOUR-ORG/operations-repo.git",
     "operations_branch": "main"
   }
   ```

### Step 2: Configure File Pulling

You have two options for pulling files:

#### Option A: Static File Mapping (Manual)

Manually specify each file to pull:

```json
{
  "engineering_paths": {
    "docs/api.md": "docs/engineering/api.md",
    "docs/architecture.md": "docs/engineering/architecture.md"
  },
  "operations_paths": {
    "docs/deployment.md": "docs/operations/deployment.md",
    "docs/monitoring.md": "docs/operations/monitoring.md"
  }
}
```

#### Option B: Pattern Matching (Recommended - Automatic)

Automatically discover files using glob patterns. New files are included automatically:

```json
{
  "engineering_patterns": [
    {
      "source": "docs/**/*.md",
      "destination": "docs/engineering/",
      "recursive": true,
      "description": "Copy all markdown files recursively from docs/ directory"
    }
  ],
  "operations_patterns": [
    {
      "source": "docs/**/*.md",
      "destination": "docs/operations/",
      "recursive": true,
      "description": "Copy all markdown files recursively from docs/ directory"
    }
  ],
  "exclude_patterns": ["*.tmp", "*.bak", "README.md"]
}
```

**Pattern Examples:**
- `docs/*.md` - All `.md` files in `docs/` directory
- `docs/**/*.md` - All `.md` files recursively in `docs/` and subdirectories
- `docs/api/*.md` - All `.md` files in `docs/api/` directory

See `scripts/CONFIG_GUIDE.md` for detailed pattern documentation.

### Step 3: Configure MkDocs

Edit `mkdocs.yml` and update:

```yaml
site_name: Your Documentation Site Name
site_description: Your documentation description
site_url: https://YOUR-ORG.github.io/REPO-NAME/
repo_name: YOUR-ORG/REPO-NAME
repo_url: https://github.com/YOUR-ORG/REPO-NAME
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test Locally

1. **Verify configuration:**
   ```bash
   python scripts/verify_setup.py
   ```

2. **Pull content from external repositories:**
   ```bash
   python scripts/pull_content.py
   ```

3. **Build documentation:**
   ```bash
   mkdocs build --strict
   ```

4. **Preview locally:**
   ```bash
   mkdocs serve
   ```
   
   Open `http://127.0.0.1:8000` in your browser to preview.

### Step 6: Deploy to GitHub

1. **Create GitHub repository** (if not already created):
   - Go to GitHub and create a new repository
   - Don't initialize with README, .gitignore, or license

2. **Initialize and push:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Central documentation setup"
   git branch -M main
   git remote add origin https://github.com/YOUR-ORG/REPO-NAME.git
   git push -u origin main
   ```

3. **Enable GitHub Pages:**
   - Go to repository **Settings** → **Pages**
   - Select **GitHub Actions** as the source

4. **Configure Secrets (if using private repos):**
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add `ENGINEERING_REPO_TOKEN` (GitHub Personal Access Token with `repo` scope)
   - Add `OPERATIONS_REPO_TOKEN` (GitHub Personal Access Token with `repo` scope)

5. **Verify deployment:**
   - Check **Actions** tab to see workflow running
   - After completion, your site will be at: `https://YOUR-ORG.github.io/REPO-NAME/`

## 📁 Project Structure

```
central-documentation/
├── docs/                      # Documentation source files
│   ├── engineering/          # Engineering docs (auto-pulled)
│   ├── operations/           # Operations docs (auto-pulled)
│   ├── asyncapi/             # AsyncAPI specifications
│   └── getting-started/      # Getting started guides
├── scripts/                  # Utility scripts
│   ├── pull_content.py      # Pull content from external repos
│   ├── verify_setup.py      # Verify configuration
│   ├── config.json          # Repository URLs and file mappings
│   └── CONFIG_GUIDE.md      # Detailed pattern configuration guide
├── .github/
│   └── workflows/
│       └── docs.yml         # GitHub Actions workflow
├── mkdocs.yml               # MkDocs configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration Files

### `scripts/config.json`

Main configuration file for repository URLs and file pulling:

- **`engineering_repo`**: URL of Engineering repository
- **`engineering_branch`**: Branch to pull from (default: `main`)
- **`engineering_paths`**: Static file mappings (optional)
- **`engineering_patterns`**: Pattern-based file matching (optional, recommended)
- **`operations_repo`**: URL of Operations repository
- **`operations_branch`**: Branch to pull from (default: `main`)
- **`operations_paths`**: Static file mappings (optional)
- **`operations_patterns`**: Pattern-based file matching (optional, recommended)
- **`exclude_patterns`**: Patterns to exclude from copying

### `mkdocs.yml`

MkDocs configuration for site name, theme, navigation, and features. See [MkDocs Documentation](https://www.mkdocs.org/) for details.

## 🔄 Automated Workflow

The GitHub Actions workflow (`.github/workflows/docs.yml`) automatically:

1. **Pulls content** from external repositories
2. **Builds** the documentation
3. **Deploys** to GitHub Pages
4. **Runs daily** at 2 AM UTC to keep content updated

## 🛠️ Common Operations

### Pull Content Manually

```bash
python scripts/pull_content.py
```

### Verify Configuration

```bash
python scripts/verify_setup.py
```

### Build Documentation

```bash
mkdocs build --strict
```

### Preview Locally

```bash
mkdocs serve
```

### Update Navigation

After adding new files, update `mkdocs.yml` navigation section:

```yaml
nav:
  - Engineering:
    - Overview: engineering/index.md
    - API: engineering/api.md
    - New File: engineering/new-file.md  # Add new pages here
```

## 🐛 Troubleshooting

### Content Not Pulling

- **Check repository URLs** in `scripts/config.json`
- **Verify file paths** exist in source repositories
- **Check authentication** for private repositories
- **Review script output** for specific error messages

### Build Failures

- **Install dependencies**: `pip install -r requirements.txt --upgrade`
- **Check MkDocs config**: `mkdocs build --strict`
- **Review workflow logs** in GitHub Actions for errors

### GitHub Pages Not Deploying

- **Verify Pages source**: Settings → Pages → Source should be "GitHub Actions"
- **Check workflow permissions**: Settings → Actions → Workflow permissions
- **Review workflow logs**: Actions tab → Check failed runs

### Private Repository Access

**For local development:**
- Use SSH URLs: `git@github.com:ORG/REPO.git`
- Or configure Git credentials

**For GitHub Actions:**
- Set up repository secrets: `ENGINEERING_REPO_TOKEN` and `OPERATIONS_REPO_TOKEN`
- Use GitHub Personal Access Tokens with `repo` scope

## 📚 Additional Resources

### Configuration Guides

- **`scripts/CONFIG_GUIDE.md`**: Detailed pattern matching documentation and examples
- **`scripts/config.example.json`**: Example configuration with all options

### External Documentation

- [MkDocs Documentation](https://www.mkdocs.org/)
- [MkDocs Material Theme](https://squidfunk.github.io/mkdocs-material/)
- [AsyncAPI Documentation](https://www.asyncapi.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)

## 📝 Maintenance

### Adding New Files

If using **pattern matching**: New files are automatically included.

If using **static mappings**: Update `scripts/config.json` and run `python scripts/pull_content.py`.

### Updating Content

Content from external repositories is automatically pulled daily. For immediate updates:

```bash
python scripts/pull_content.py
git add docs/
git commit -m "Update documentation from external repos"
git push
```

### Customizing Theme

Edit `mkdocs.yml` theme section:

```yaml
theme:
  name: material
  palette:
    - scheme: default
      primary: indigo  # Change to your brand color
      accent: indigo
```

## ✅ Pre-Deployment Checklist

- [ ] Updated all `your-org` placeholders in `scripts/config.json`
- [ ] Updated all `your-org` placeholders in `mkdocs.yml`
- [ ] Verified file paths/patterns match source repositories
- [ ] Ran `python scripts/verify_setup.py` successfully
- [ ] Tested `python scripts/pull_content.py` locally
- [ ] Built documentation: `mkdocs build --strict` (no errors)
- [ ] Previewed locally: `mkdocs serve` (all pages work)
- [ ] Created GitHub repository
- [ ] Enabled GitHub Pages with GitHub Actions source
- [ ] Configured secrets for private repositories (if needed)
- [ ] Pushed code to GitHub
- [ ] Verified workflow runs successfully
- [ ] Site accessible at GitHub Pages URL

## 🎯 Quick Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Verify setup
python scripts/verify_setup.py

# Pull content
python scripts/pull_content.py

# Build documentation
mkdocs build --strict

# Preview locally
mkdocs serve

# Deploy (after git setup)
git add .
git commit -m "Update documentation"
git push
```

---

**Need help?** Check the troubleshooting section above or review the configuration guides in the `scripts/` directory.

**Last Updated**: 01-12-2026

