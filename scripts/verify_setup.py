#!/usr/bin/env python3
"""
Verification script to check if the documentation setup is ready for production.
Run this script before deploying to ensure everything is configured correctly.
"""

import json
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if filepath.exists():
        print(f"[OK] {description}: {filepath}")
        return True
    else:
        print(f"[FAIL] {description}: {filepath} - NOT FOUND")
        return False


def check_json_valid(filepath, description):
    """Check if a JSON file is valid"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"[OK] {description}: Valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"[FAIL] {description}: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"[FAIL] {description}: Error reading file - {e}")
        return False


def check_config_placeholders(config_path):
    """Check if config.json has placeholder values"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        issues = []
        
        # Check for placeholder values
        if "your-org" in config.get("engineering_repo", ""):
            issues.append("engineering_repo contains 'your-org' placeholder")
        
        if "your-org" in config.get("operations_repo", ""):
            issues.append("operations_repo contains 'your-org' placeholder")
        
        # Check required fields
        required_fields = ["engineering_repo", "operations_repo", "engineering_paths", "operations_paths"]
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")
        
        if issues:
            print(f"[WARNING] Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("[OK] Configuration looks good (no placeholders detected)")
            return True
            
    except Exception as e:
        print(f"✗ Error checking configuration: {e}")
        return False


def check_mkdocs_placeholders(mkdocs_path):
    """Check if mkdocs.yml has placeholder values"""
    try:
        with open(mkdocs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        if "your-org" in content:
            issues.append("mkdocs.yml contains 'your-org' placeholder(s)")
        
        if "Central Documentation" in content and "site_name" in content:
            # This is likely a placeholder unless they actually named it that
            pass  # Not strictly an issue
        
        if issues:
            print(f"[WARNING] MkDocs configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("[OK] MkDocs configuration looks good")
            return True
            
    except Exception as e:
        print(f"✗ Error checking MkDocs configuration: {e}")
        return False


def check_docs_structure(docs_path):
    """Check if required documentation files exist"""
    required_files = [
        "index.md",
        "getting-started/overview.md",
        "getting-started/setup.md",
        "engineering/index.md",
        "operations/index.md",
        "asyncapi/index.md",
    ]
    
    all_exist = True
    for file_rel in required_files:
        file_path = docs_path / file_rel
        if file_path.exists():
            print(f"[OK] Documentation file exists: {file_rel}")
        else:
            print(f"[FAIL] Documentation file missing: {file_rel}")
            all_exist = False
    
    return all_exist


def main():
    """Main verification function"""
    print("=" * 70)
    print("Documentation Setup Verification")
    print("=" * 70)
    print()
    
    base_path = Path(__file__).parent.parent
    results = []
    
    # Check required files
    print("[1/6] Checking required files...")
    print("-" * 70)
    results.append(check_file_exists(base_path / "mkdocs.yml", "MkDocs configuration"))
    results.append(check_file_exists(base_path / "requirements.txt", "Requirements file"))
    results.append(check_file_exists(base_path / "scripts" / "config.json", "Configuration file"))
    results.append(check_file_exists(base_path / "scripts" / "pull_content.py", "Content pull script"))
    results.append(check_file_exists(base_path / ".github" / "workflows" / "docs.yml", "GitHub Actions workflow"))
    results.append(check_file_exists(base_path / ".gitignore", "Git ignore file"))
    print()
    
    # Check JSON validity
    print("[2/6] Checking JSON files...")
    print("-" * 70)
    results.append(check_json_valid(base_path / "scripts" / "config.json", "config.json"))
    print()
    
    # Check configuration placeholders
    print("[3/6] Checking for placeholder values in configuration...")
    print("-" * 70)
    results.append(check_config_placeholders(base_path / "scripts" / "config.json"))
    print()
    
    # Check MkDocs placeholders
    print("[4/6] Checking for placeholder values in mkdocs.yml...")
    print("-" * 70)
    results.append(check_mkdocs_placeholders(base_path / "mkdocs.yml"))
    print()
    
    # Check documentation structure
    print("[5/6] Checking documentation structure...")
    print("-" * 70)
    results.append(check_docs_structure(base_path / "docs"))
    print()
    
    # Check Python script syntax
    print("[6/6] Checking Python script syntax...")
    print("-" * 70)
    try:
        import py_compile
        py_compile.compile(str(base_path / "scripts" / "pull_content.py"), doraise=True)
        print("[OK] Python script syntax is valid")
        results.append(True)
    except py_compile.PyCompileError as e:
        print(f"[FAIL] Python script syntax error: {e}")
        results.append(False)
    except Exception as e:
        print(f"[WARNING] Could not verify Python script syntax: {e}")
        results.append(False)
    print()
    
    # Summary
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total} checks")
    
    if passed == total:
        print("\n[SUCCESS] All checks passed! Your setup looks ready for deployment.")
        print("\nNext steps:")
        print("  1. Review DEPLOYMENT.md for detailed deployment steps")
        print("  2. Test locally: python scripts/pull_content.py")
        print("  3. Build documentation: mkdocs build --strict")
        print("  4. Preview locally: mkdocs serve")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} check(s) failed. Please review the issues above.")
        print("\nBefore deploying:")
        print("  1. Fix all issues listed above")
        print("  2. Update placeholder values in configuration files")
        print("  3. Verify all required files exist")
        print("  4. Run this verification again")
        return 1


if __name__ == "__main__":
    sys.exit(main())

