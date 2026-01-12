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


def clone_or_update_repo(repo_url, branch, temp_path, repo_name, token=None):
    """Clone or update a repository"""
    repo_path = temp_path / repo_name
    
    if repo_path.exists():
        print(f"Updating {repo_name} repository...")
        try:
            result = subprocess.run(
                ["git", "pull", "origin", branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
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
        if token:
            if repo_url.startswith("https://"):
                # Insert token into HTTPS URL
                repo_url = repo_url.replace("https://", f"https://{token}@")
            elif repo_url.startswith("git@"):
                # For SSH URLs, token won't work - use SSH keys instead
                print(f"Warning: Token authentication not supported for SSH URLs. Using SSH keys.")
        
        result = subprocess.run(
            ["git", "clone", "-b", branch, "--depth", "1", repo_url, str(target_path)],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to clone repository {repo_url}")
        error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='ignore')
        print(f"Error details: {error_msg}")
        
        # Check if it's an authentication error
        if "authentication" in error_msg.lower() or "permission" in error_msg.lower():
            print("\n💡 Tip: If this is a private repository, you may need to:")
            print("   1. Configure SSH keys, or")
            print("   2. Use a personal access token in the repository URL, or")
            print("   3. Set up repository secrets in GitHub Actions")
        
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
            parent_dir = source_path_obj.parent
            pattern_name = source_path_obj.name
            
            if not parent_dir.exists():
                print(f"  [WARNING] Source directory does not exist: {parent_dir.relative_to(source_repo_path)}")
                continue
            
            # Find matching files
            matching_files = []
            if pattern_config.get("recursive", False) or "**" in source_pattern:
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
            
            # Copy file
            try:
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
    
    # Process messaging-core repository
    if "messaging_core_repo" in config and repos_to_pull["messaging_core"]:
        print(f"\n[1/2] Processing messaging-core Repository...")
        messaging_core_repo_path = clone_or_update_repo(
            config["messaging_core_repo"],
            config.get("messaging_core_branch", "main"),
            temp_path,
            "engineering",
            messaging_core_token
        )
        
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
        virtual_golf_game_api_repo_path = clone_or_update_repo(
            config["virtual_golf_game_api_repo"],
            config.get("virtual_golf_game_api_branch", "main"),
            temp_path,
            "operations",
            virtual_golf_game_api_token
        )
        
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


if __name__ == "__main__":
    main()

