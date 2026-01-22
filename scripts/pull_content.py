#!/usr/bin/env python3
"""
Script to pull content from Engineering and Operations repositories
and copy specific files to the central documentation repository.
"""

import json
import os
import shutil
import subprocess
import sys
import fnmatch
from pathlib import Path


def load_config():
    """Load configuration from config.json"""
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.json"
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ["messaging_core_repo", "virtual_golf_game_api_repo"]
        for field in required_fields:
            if field not in config:
                print(f"Warning: Missing field '{field}' in config.json")
        
        return config
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config.json: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load config.json: {e}")
        sys.exit(1)


def ensure_temp_dir(temp_dir):
    """Ensure temporary directory exists"""
    temp_path = Path(temp_dir)
    if temp_path.exists():
        shutil.rmtree(temp_path)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


def clone_or_update_repo(repo_url, branch, temp_path, repo_name, token=None, commit_sha=None):
    """Clone or update a repository, optionally checking out a specific commit"""
    repo_path = temp_path / repo_name
    
    # Always clone fresh when using specific commit SHA
    if commit_sha:
        if repo_path.exists():
            shutil.rmtree(repo_path)
        print(f"Cloning {repo_name} repository to checkout commit {commit_sha[:7]}...")
        clone_repo(repo_url, branch, repo_path, token)
        
        # Checkout the specific commit
        try:
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            env['GIT_ASKPASS'] = 'echo'
            result = subprocess.run(
                ["git", "checkout", commit_sha],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
                env=env
            )
            print(f"  ✅ Checked out commit {commit_sha[:7]}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='ignore')
            print(f"  ⚠️  Warning: Failed to checkout commit {commit_sha[:7]}: {error_msg}")
            print(f"  → Will use latest branch ({branch}) instead")
    else:
        # Standard clone/update behavior for scheduled or manual triggers
        if repo_path.exists():
            print(f"Updating {repo_name} repository...")
            try:
                env = os.environ.copy()
                env['GIT_TERMINAL_PROMPT'] = '0'
                result = subprocess.run(
                    ["git", "pull", "origin", branch],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env
                )
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='ignore')
                print(f"Warning: Failed to update {repo_name} repo: {error_msg}")
                print(f"Attempting fresh clone...")
                shutil.rmtree(repo_path)
                clone_repo(repo_url, branch, repo_path, token)
        else:
            print(f"Cloning {repo_name} repository...")
            clone_repo(repo_url, branch, repo_path, token)
    
    return repo_path


def clone_repo(repo_url, branch, target_path, token=None):
    """Clone a repository to a specific path"""
    try:
        # If token is provided, inject it into the URL for authentication
        authenticated_url = repo_url
        if token and token.strip():
            if repo_url.startswith("https://"):
                # For GitHub, use token as username in HTTPS URL
                # Format: https://<token>@github.com/org/repo.git
                if "github.com" in repo_url:
                    authenticated_url = repo_url.replace("https://", f"https://{token}@")
                else:
                    # For other Git hosts, use token as username
                    authenticated_url = repo_url.replace("https://", f"https://{token}@")
            elif repo_url.startswith("git@"):
                # For SSH URLs, token won't work - use SSH keys instead
                print(f"Warning: Token authentication not supported for SSH URLs. Using SSH keys.")
                authenticated_url = repo_url
        else:
            # Check if this is a private repository that needs authentication
            if "github.com" in repo_url and not repo_url.startswith("git@"):
                print(f"⚠️  Warning: No authentication token provided for {repo_url}")
                print(f"   If this is a private repository, set MESSAGING_CORE_REPO_TOKEN or VIRTUAL_GOLF_GAME_API_REPO_TOKEN")
        
        # Configure Git to not prompt for credentials
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        env['GIT_ASKPASS'] = 'echo'
        
        result = subprocess.run(
            ["git", "clone", "-b", branch, "--depth", "1", authenticated_url, str(target_path)],
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        print(f"  ✅ Successfully cloned {repo_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Failed to clone repository {repo_url}")
        error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='ignore')
        stdout_msg = e.stdout if isinstance(e.stdout, str) else e.stdout.decode('utf-8', errors='ignore') if e.stdout else ""
        print(f"Error details: {error_msg}")
        if stdout_msg:
            print(f"Output: {stdout_msg}")
        
        # Check for specific authentication errors
        error_lower = error_msg.lower()
        if "could not read username" in error_lower or "authentication" in error_lower or "permission" in error_lower or "credential" in error_lower:
            print("\n🔐 Authentication Error Detected")
            print("💡 Solution: Add GitHub Personal Access Token as repository secret")
            print("\n   For messaging-core repository:")
            print("   - Secret name: MESSAGING_CORE_REPO_TOKEN")
            print("   - Token scopes needed: 'repo' (for private repos)")
            print("\n   For virtual-golf-game-api repository:")
            print("   - Secret name: VIRTUAL_GOLF_GAME_API_REPO_TOKEN")
            print("   - Token scopes needed: 'repo' (for private repos)")
            print("\n   Steps:")
            print("   1. Create token: GitHub → Settings → Developer settings → Personal access tokens")
            print("   2. Add token to central documentation repo → Settings → Secrets → Actions")
            print("   3. Make sure token has 'repo' scope if repositories are private")
        
        sys.exit(1)


def should_exclude_file(file_path, exclude_patterns):
    """Check if a file should be excluded based on patterns"""
    if not exclude_patterns:
        return False
    
    file_name = file_path.name
    file_path_str = str(file_path)
    
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_path_str, pattern):
            return True
    return False


def is_yaml_file(file_path):
    """Return True for YAML files."""
    suffix = file_path.suffix.lower()
    return suffix in {".yml", ".yaml"}


def write_yaml_markdown(source_file, dest_md, relative_source):
    """Create a readable Markdown wrapper for YAML content."""
    try:
        yaml_content = source_file.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        print(f"  [ERROR] Failed to read {relative_source}: {e}")
        return False

    dest_md.parent.mkdir(parents=True, exist_ok=True)
    title = f"{source_file.name}"
    markdown = (
        f"# {title}\n\n"
        f"Source: `{relative_source}`\n\n"
        "```yaml\n"
        f"{yaml_content}\n"
        "```\n"
    )
    try:
        dest_md.write_text(markdown, encoding="utf-8")
        return True
    except OSError as e:
        print(f"  [ERROR] Failed to write {dest_md}: {e}")
        return False


def match_file_to_pattern(file_path, pattern_config, exclude_patterns):
    """Check if a file matches a pattern configuration"""
    source_pattern = pattern_config.get("source")
    
    # Convert Path object to string and normalize
    if isinstance(file_path, Path):
        file_path_str = str(file_path).replace("\\", "/")
    else:
        file_path_str = str(file_path).replace("\\", "/")
    
    # Normalize pattern
    source_pattern = source_pattern.replace("\\", "/")
    
    # Check exclusions first (convert Path to string for exclusion check)
    if should_exclude_file(Path(file_path_str) if not isinstance(file_path, Path) else file_path, exclude_patterns):
        return False
    
    # Handle glob patterns
    if "*" in source_pattern or "?" in source_pattern:
        # For recursive patterns (**)
        if "**" in source_pattern:
            # Convert ** pattern to fnmatch pattern
            # docs/**/*.md should match docs/any/path/file.md
            pattern_parts = source_pattern.split("**")
            if len(pattern_parts) == 2:
                prefix = pattern_parts[0].rstrip("/")
                suffix = pattern_parts[1].lstrip("/")
                if not prefix:
                    # **/*.md - match any file with that extension
                    if fnmatch.fnmatch(file_path_str, f"*{suffix}") or fnmatch.fnmatch(file_path.name, suffix):
                        return True
                elif file_path_str.startswith(prefix):
                    # docs/**/*.md - match docs/.../*.md
                    remaining = file_path_str[len(prefix):].lstrip("/")
                    if fnmatch.fnmatch(remaining, suffix) or fnmatch.fnmatch(remaining, f"*/{suffix}") or fnmatch.fnmatch(remaining, f"**/{suffix}"):
                        return True
            else:
                # Multiple **, use simpler matching
                if fnmatch.fnmatch(file_path_str, source_pattern.replace("**", "*")):
                    return True
        else:
            # Simple glob pattern (no **)
            if fnmatch.fnmatch(file_path_str, source_pattern):
                return True
    else:
        # Exact match (no wildcards)
        if file_path_str == source_pattern or file_path.name == source_pattern:
            return True
        # Also check if it's a directory pattern match
        if source_pattern.endswith("/") and file_path_str.startswith(source_pattern.rstrip("/")):
            return True
    
    return False


def copy_changed_files(source_repo_path, changed_files_list, patterns, exclude_patterns, repo_name):
    """Copy only the changed files that match the patterns"""
    base_path = Path(__file__).parent.parent
    docs_path = base_path / "docs"
    
    if not changed_files_list:
        print("  [INFO] No changed files list provided")
        return 0
    
    # Parse changed files (comma-separated)
    changed_files = [f.strip() for f in changed_files_list.split(",") if f.strip()]
    
    if not changed_files:
        print("  [INFO] No changed files to process")
        return 0
    
    print(f"  Processing {len(changed_files)} changed file(s)...")
    
    copied_count = 0
    matched_files = []
    
    # Find which changed files match our patterns
    for changed_file in changed_files:
        # Normalize path (handle both Windows and Unix paths)
        changed_file_normalized = changed_file.replace("\\", "/")
        file_path = source_repo_path / changed_file_normalized
        
        # Check if file exists (might have been deleted)
        if not file_path.exists():
            print(f"  [INFO] File no longer exists (deleted?): {changed_file}")
            # TODO: Could delete from destination if needed
            continue
        
        # Get relative path for pattern matching (relative to repo root)
        try:
            relative_path = file_path.relative_to(source_repo_path)
        except ValueError:
            # If path is not relative, try to make it relative
            relative_path = Path(changed_file_normalized)
        
        # Check if file matches any pattern
        for pattern_config in patterns:
            dest_base = pattern_config.get("destination", "")
            
            # Use the actual file path for matching (pathlib Path object)
            if match_file_to_pattern(relative_path, pattern_config, exclude_patterns):
                matched_files.append((file_path, dest_base, changed_file_normalized))
                break
    
    # Copy matched files
    for source_file, dest_base, relative_path in matched_files:
        # Determine destination path
        if dest_base.endswith("/") or dest_base == "":
            # Destination is a directory, preserve relative path structure
            dest_file = docs_path / dest_base / relative_path
        else:
            # Destination is a specific file path
            dest_file = docs_path / dest_base
        
        # Ensure destination directory exists
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file (render YAML to Markdown instead of copying raw YAML)
        try:
            if is_yaml_file(source_file):
                dest_md = dest_file.with_suffix(dest_file.suffix + ".md")
                if write_yaml_markdown(source_file, dest_md, relative_path):
                    print(f"  [OK] Rendered {relative_path} -> {dest_md.relative_to(docs_path)}")
                    copied_count += 1
            else:
                shutil.copy2(source_file, dest_file)
                print(f"  [OK] Copied {relative_path} -> {dest_file.relative_to(docs_path)}")
                copied_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to copy {relative_path}: {e}")
    
    if not matched_files:
        print(f"  [INFO] No changed files matched the configured patterns")
        print(f"  Changed files: {', '.join(changed_files[:5])}{'...' if len(changed_files) > 5 else ''}")
    
    return copied_count


def copy_files_by_pattern(source_repo_path, patterns, exclude_patterns, repo_name):
    """Copy files from source repository using glob patterns"""
    base_path = Path(__file__).parent.parent
    docs_path = base_path / "docs"
    
    copied_count = 0
    
    for pattern_config in patterns:
        source_pattern = pattern_config.get("source")
        dest_base = pattern_config.get("destination", "")
        description = pattern_config.get("description", "")
        
        if description:
            print(f"  Pattern: {description}")
        
        # Convert glob pattern to Path pattern
        source_path_obj = source_repo_path / source_pattern
        
        # Find all matching files
        if "*" in source_pattern or "?" in source_pattern:
            # Use glob pattern matching
            matching_files = []
            if "**" in source_pattern:
                # Handle recursive patterns without treating '**' as a real folder
                prefix, _, suffix = source_pattern.partition("**")
                base_dir = prefix.rstrip("/")
                pattern_name = suffix.lstrip("/") or "*"
                parent_dir = source_repo_path / base_dir if base_dir else source_repo_path
                
                if not parent_dir.exists():
                    print(f"  [WARNING] Source directory does not exist: {parent_dir.relative_to(source_repo_path)}")
                    continue
                
                for file_path in parent_dir.rglob(pattern_name):
                    if file_path.is_file() and not should_exclude_file(file_path, exclude_patterns):
                        matching_files.append(file_path)
            else:
                parent_dir = source_path_obj.parent
                pattern_name = source_path_obj.name
                
                if not parent_dir.exists():
                    print(f"  [WARNING] Source directory does not exist: {parent_dir.relative_to(source_repo_path)}")
                    continue
                
                if pattern_config.get("recursive", False):
                    # Recursive search
                    for file_path in parent_dir.rglob(pattern_name):
                        if file_path.is_file() and not should_exclude_file(file_path, exclude_patterns):
                            matching_files.append(file_path)
                else:
                    # Non-recursive search
                    for file_path in parent_dir.glob(pattern_name):
                        if file_path.is_file() and not should_exclude_file(file_path, exclude_patterns):
                            matching_files.append(file_path)
        else:
            # Single file or directory
            if source_path_obj.exists():
                matching_files = [source_path_obj] if source_path_obj.is_file() else list(source_path_obj.rglob("*")) if source_path_obj.is_dir() else []
                matching_files = [f for f in matching_files if f.is_file() and not should_exclude_file(f, exclude_patterns)]
        
        # Copy matching files
        for source_file in matching_files:
            relative_path = source_file.relative_to(source_repo_path)
            
            # Determine destination path
            if dest_base.endswith("/") or dest_base == "":
                # Destination is a directory, preserve relative path structure
                if source_pattern.endswith("/") or source_path_obj.is_dir():
                    # Preserve directory structure
                    dest_file = docs_path / dest_base / relative_path
                else:
                    # Just use the filename
                    dest_file = docs_path / dest_base / source_file.name
            else:
                # Destination is a specific file path
                dest_file = docs_path / dest_base
            
            # Ensure destination directory exists
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file (render YAML to Markdown instead of copying raw YAML)
            try:
                if is_yaml_file(source_file):
                    dest_md = dest_file.with_suffix(dest_file.suffix + ".md")
                    if write_yaml_markdown(source_file, dest_md, relative_path):
                        print(f"  [OK] Rendered {relative_path} -> {dest_md.relative_to(docs_path)}")
                        copied_count += 1
                else:
                    shutil.copy2(source_file, dest_file)
                    print(f"  [OK] Copied {relative_path} -> {dest_file.relative_to(docs_path)}")
                    copied_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to copy {relative_path}: {e}")
        
        if not matching_files:
            print(f"  [INFO] No files matched pattern: {source_pattern}")
    
    return copied_count


def copy_files(source_repo_path, file_mapping, repo_name):
    """Copy files from source repository to documentation structure (static mapping)"""
    base_path = Path(__file__).parent.parent
    docs_path = base_path / "docs"
    
    copied_count = 0
    for source_path, dest_path in file_mapping.items():
        source_file = source_repo_path / source_path
        dest_file = docs_path / dest_path
        
        if source_file.exists():
            # Ensure destination directory exists
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_file, dest_file)
            print(f"  [OK] Copied {source_path} -> {dest_path}")
            copied_count += 1
        else:
            print(f"  [WARNING] Source file not found: {source_path}")
    
    return copied_count


def determine_repos_to_pull(config):
    """
    Determine which repositories to pull based on environment variables.
    Returns a dict with flags for each repo.
    """
    # Get the triggering repository from environment (set by GitHub Actions)
    trigger_repo = os.environ.get("TRIGGER_REPOSITORY", "").lower()
    
    # Default: pull from both repos (for cron, push, manual triggers)
    pull_messaging_core = True
    pull_virtual_golf_game_api = True
    
    # If triggered by repository_dispatch, only pull from the triggering repo
    if trigger_repo:
        print(f"📥 Triggered by repository: {trigger_repo}")
        
        # Check if it's messaging-core
        if "messaging-core" in trigger_repo or "messaging_core" in trigger_repo:
            pull_messaging_core = True
            pull_virtual_golf_game_api = False
            print("  → Will pull from: messaging-core only")
        # Check if it's virtual-golf-game-api
        elif "virtual-golf-game-api" in trigger_repo or "virtual_golf_game_api" in trigger_repo:
            pull_messaging_core = False
            pull_virtual_golf_game_api = True
            print("  → Will pull from: virtual-golf-game-api only")
        else:
            # Unknown repo, pull from both to be safe
            print(f"  ⚠️  Unknown repository '{trigger_repo}', will pull from both repos")
    else:
        print("📥 No specific repository trigger detected, will pull from both repos")
    
    return {
        "messaging_core": pull_messaging_core,
        "virtual_golf_game_api": pull_virtual_golf_game_api
    }


def main():
    """Main function to pull content from repositories"""
    print("=" * 60)
    print("Pulling Content from External Repositories")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    
    # Determine which repos to pull based on trigger
    repos_to_pull = determine_repos_to_pull(config)
    
    # Setup temporary directory
    temp_dir = config.get("temp_dir", ".temp_repos")
    temp_path = ensure_temp_dir(temp_dir)
    
    total_copied = 0
    
    # Get authentication tokens from environment variables (for GitHub Actions)
    messaging_core_token = os.environ.get("MESSAGING_CORE_REPO_TOKEN")
    virtual_golf_game_api_token = os.environ.get("VIRTUAL_GOLF_GAME_API_REPO_TOKEN")
    
    # Get commit info if triggered by repository_dispatch
    trigger_commit = os.environ.get("TRIGGER_COMMIT", "")
    trigger_changed_files = os.environ.get("TRIGGER_CHANGED_FILES", "")
    trigger_repo = os.environ.get("TRIGGER_REPOSITORY", "").lower()
    
    # Determine if we should use commit-based pulling (only for repository_dispatch)
    use_commit_based = bool(trigger_commit and trigger_changed_files)
    
    if use_commit_based:
        print(f"\n📋 Commit-based pulling mode enabled")
        print(f"   Commit: {trigger_commit[:7] if trigger_commit else 'N/A'}")
        print(f"   Changed files: {len(trigger_changed_files.split(',')) if trigger_changed_files else 0} file(s)")
    
    # Process messaging-core repository
    if "messaging_core_repo" in config and repos_to_pull["messaging_core"]:
        print(f"\n[1/2] Processing messaging-core Repository...")
        
        # Get commit SHA if this is the triggering repo
        commit_sha = trigger_commit if use_commit_based and "messaging-core" in trigger_repo else None
        changed_files_list = trigger_changed_files if use_commit_based and "messaging-core" in trigger_repo else None
        
        messaging_core_repo_path = clone_or_update_repo(
            config["messaging_core_repo"],
            config.get("messaging_core_branch", "main"),
            temp_path,
            "engineering",
            messaging_core_token,
            commit_sha=commit_sha
        )
        
        # Use commit-based copying if available, otherwise use pattern-based
        copied = 0
        if changed_files_list and "messaging_core_patterns" in config and config["messaging_core_patterns"]:
            print("  Copying only changed files that match patterns...")
            exclude_patterns = config.get("exclude_patterns", [])
            copied = copy_changed_files(
                messaging_core_repo_path,
                changed_files_list,
                config["messaging_core_patterns"],
                exclude_patterns,
                "messaging-core"
            )
            total_copied += copied

        # Fallback if commit-based copy finds nothing (common on squash/merge commits)
        if copied == 0:
            # Fallback to pattern-based or static mapping (for scheduled/push/manual triggers)
            # Process static file mappings (backward compatibility)
            if "messaging_core_paths" in config and config["messaging_core_paths"]:
                print("  Copying static file mappings...")
                copied = copy_files(
                    messaging_core_repo_path,
                    config["messaging_core_paths"],
                    "messaging-core"
                )
                total_copied += copied
            
            # Process pattern-based file copying (dynamic)
            if "messaging_core_patterns" in config and config["messaging_core_patterns"]:
                print("  Copying files using patterns...")
                exclude_patterns = config.get("exclude_patterns", [])
                copied = copy_files_by_pattern(
                    messaging_core_repo_path,
                    config["messaging_core_patterns"],
                    exclude_patterns,
                    "messaging-core"
                )
                total_copied += copied
    elif repos_to_pull["messaging_core"]:
        print("\n⚠️  Warning: messaging-core repository not configured in config.json")
    else:
        print("\n⏭️  Skipping messaging-core (not triggered by this repository)")
    
    # Process virtual-golf-game-api repository
    if "virtual_golf_game_api_repo" in config and repos_to_pull["virtual_golf_game_api"]:
        print(f"\n[2/2] Processing virtual-golf-game-api Repository...")
        
        # Get commit SHA if this is the triggering repo
        commit_sha = trigger_commit if use_commit_based and "virtual-golf-game-api" in trigger_repo else None
        changed_files_list = trigger_changed_files if use_commit_based and "virtual-golf-game-api" in trigger_repo else None
        
        virtual_golf_game_api_repo_path = clone_or_update_repo(
            config["virtual_golf_game_api_repo"],
            config.get("virtual_golf_game_api_branch", "main"),
            temp_path,
            "operations",
            virtual_golf_game_api_token,
            commit_sha=commit_sha
        )
        
        # Use commit-based copying if available, otherwise use pattern-based
        copied = 0
        if changed_files_list and "virtual_golf_game_api_patterns" in config and config["virtual_golf_game_api_patterns"]:
            print("  Copying only changed files that match patterns...")
            exclude_patterns = config.get("exclude_patterns", [])
            copied = copy_changed_files(
                virtual_golf_game_api_repo_path,
                changed_files_list,
                config["virtual_golf_game_api_patterns"],
                exclude_patterns,
                "virtual-golf-game-api"
            )
            total_copied += copied

        # Fallback if commit-based copy finds nothing (common on squash/merge commits)
        if copied == 0:
            # Fallback to pattern-based or static mapping (for scheduled/push/manual triggers)
            # Process static file mappings (backward compatibility)
            if "virtual_golf_game_api_paths" in config and config["virtual_golf_game_api_paths"]:
                print("  Copying static file mappings...")
                copied = copy_files(
                    virtual_golf_game_api_repo_path,
                    config["virtual_golf_game_api_paths"],
                    "virtual-golf-game-api"
                )
                total_copied += copied
            
            # Process pattern-based file copying (dynamic)
            if "virtual_golf_game_api_patterns" in config and config["virtual_golf_game_api_patterns"]:
                print("  Copying files using patterns...")
                exclude_patterns = config.get("exclude_patterns", [])
                copied = copy_files_by_pattern(
                    virtual_golf_game_api_repo_path,
                    config["virtual_golf_game_api_patterns"],
                    exclude_patterns,
                    "virtual-golf-game-api"
                )
                total_copied += copied
    elif repos_to_pull["virtual_golf_game_api"]:
        print("\n⚠️  Warning: virtual-golf-game-api repository not configured in config.json")
    else:
        print("\n⏭️  Skipping virtual-golf-game-api (not triggered by this repository)")
    
    # Cleanup temporary directory
    print(f"\nCleaning up temporary files...")
    shutil.rmtree(temp_path)
    
    # Summary
    print("\n" + "=" * 60)
    if total_copied > 0:
        print(f"[SUCCESS] Successfully copied {total_copied} file(s)")
    else:
        print("[WARNING] No files were copied. Check your configuration.")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review the copied files in the docs/ directory")
    print("  2. Update mkdocs.yml navigation if new files were added")
    print("  3. Build the documentation: mkdocs build")
    print("  4. Serve locally: mkdocs serve")

    # Clean up any raw YAML files under docs/ to avoid mkdocs path collisions
    docs_root = Path(__file__).parent.parent / "docs"
    if docs_root.exists():
        removed_yaml = 0
        for yaml_path in docs_root.rglob("*"):
            if yaml_path.is_file() and yaml_path.suffix.lower() in {".yml", ".yaml"}:
                try:
                    yaml_path.unlink()
                    removed_yaml += 1
                except OSError as e:
                    print(f"[WARNING] Failed to remove {yaml_path}: {e}")
        if removed_yaml:
            print(f"[INFO] Removed {removed_yaml} raw YAML file(s) from docs/")


if __name__ == "__main__":
    main()

