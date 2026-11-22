#!/usr/bin/env python3
"""
Environment Verification Script for Testing Agent Platform.
Checks virtual environment isolation, Python version, dependencies,
environment variables, and project structure.
"""

import sys
import os
import subprocess
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

REQUIRED_PYTHON_MAJOR = 3
REQUIRED_PYTHON_MINOR = 11

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "dotenv",  # python-dotenv maps to dotenv or importlib distribution python-dotenv
    "httpx",
    "pytest",
]

EXPECTED_FILES = [
    "requirements.txt",
    "requirements-dev.txt",
    ".gitignore",
    ".env",
    ".env.example",
    "scripts/check_environment.py",
]

EXPECTED_ENV_VARS = [
    "ENVIRONMENT",
    "APP_HOST",
    "APP_PORT",
]


def print_header(title: str):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def check_virtual_env() -> bool:
    """Verifies that the script is executing inside a Python virtual environment."""
    is_venv = (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or "VIRTUAL_ENV" in os.environ
    )
    print(f"Interpreter: {sys.executable}")
    print(f"Prefix:      {sys.prefix}")
    print(f"Base Prefix: {sys.base_prefix}")

    # Check if executable path belongs to .venv
    norm_exec = os.path.normcase(os.path.abspath(sys.executable))
    norm_prefix = os.path.normcase(os.path.abspath(sys.prefix))
    in_dot_venv = ".venv" in norm_exec or ".venv" in norm_prefix

    if not is_venv:
        print("[FAIL] Not running inside a virtual environment! System Python detected.")
        return False

    if not in_dot_venv:
        print(f"[WARNING] Running in a virtual environment, but path does not contain '.venv': {sys.prefix}")
    else:
        print("[PASS] Running inside dedicated project virtual environment (.venv).")

    return True


def check_python_version() -> bool:
    """Verifies that Python version is >= 3.11."""
    major, minor, micro = sys.version_info[:3]
    version_str = f"{major}.{minor}.{micro}"
    print(f"Python Version: {version_str}")

    if major < REQUIRED_PYTHON_MAJOR or (major == REQUIRED_PYTHON_MAJOR and minor < REQUIRED_PYTHON_MINOR):
        print(f"[FAIL] Python {REQUIRED_PYTHON_MAJOR}.{REQUIRED_PYTHON_MINOR}+ is required. Found: {version_str}")
        return False

    print(f"[PASS] Python version {version_str} meets requirement (>={REQUIRED_PYTHON_MAJOR}.{REQUIRED_PYTHON_MINOR}).")
    return True


def check_pip() -> bool:
    """Verifies pip is installed and functional within the virtual environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        pip_version_str = result.stdout.strip()
        print(f"pip version: {pip_version_str}")
        print("[PASS] pip is accessible and functional inside virtual environment.")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to run pip via active interpreter: {e}")
        return False


def check_packages() -> bool:
    """Checks whether required packages are installed."""
    all_ok = True
    dist_map = {
        "dotenv": "python-dotenv",
    }

    for pkg in REQUIRED_PACKAGES:
        dist_name = dist_map.get(pkg, pkg)
        try:
            installed_ver = version(dist_name)
            print(f"  - {dist_name}: {installed_ver} [INSTALLED]")
        except PackageNotFoundError:
            print(f"  - {dist_name}: MISSING [NOT INSTALLED]")
            all_ok = False

    if all_ok:
        print("[PASS] All required core packages are installed.")
    else:
        print("[FAIL] Missing one or more required packages. Run `python -m pip install -r requirements-dev.txt`.")
    return all_ok


def check_env_loading(project_root: Path) -> bool:
    """Tests loading .env via python-dotenv and checks required environment variables."""
    try:
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if not env_path.exists():
            print(f"[FAIL] .env file not found at {env_path}")
            return False

        load_dotenv(dotenv_path=env_path, override=True)
        missing = []
        for var in EXPECTED_ENV_VARS:
            val = os.getenv(var)
            if val is None or val == "":
                missing.append(var)
            else:
                print(f"  - {var}={val}")

        if missing:
            print(f"[FAIL] Missing environment variables in .env: {', '.join(missing)}")
            return False

        print("[PASS] .env file loaded successfully and contains expected variables.")
        return True
    except Exception as e:
        print(f"[FAIL] Error loading .env: {e}")
        return False


def check_directory_structure(project_root: Path) -> bool:
    """Verifies presence of expected project files and directories."""
    all_ok = True
    for relative_path in EXPECTED_FILES:
        full_path = project_root / relative_path
        if full_path.exists():
            print(f"  - [FOUND] {relative_path}")
        else:
            print(f"  - [MISSING] {relative_path}")
            all_ok = False

    if all_ok:
        print("[PASS] All essential project files and directories exist.")
    else:
        print("[FAIL] Some expected project files are missing.")
    return all_ok


def check_gitignore_rules(project_root: Path) -> bool:
    """Verifies that .gitignore includes .venv and .env."""
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        print("[FAIL] .gitignore does not exist.")
        return False

    content = gitignore_path.read_text(encoding="utf-8")
    has_venv = ".venv" in content
    has_env = ".env" in content

    if has_venv and has_env:
        print("[PASS] .gitignore properly excludes .venv and .env.")
        return True
    else:
        missing = []
        if not has_venv:
            missing.append(".venv")
        if not has_env:
            missing.append(".env")
        print(f"[FAIL] .gitignore is missing rules for: {', '.join(missing)}")
        return False


def main():
    print_header("Testing Agent Platform - Environment Verification")
    
    # Determine project root (parent directory of scripts/)
    current_script = Path(__file__).resolve()
    project_root = current_script.parent.parent
    print(f"Project Root: {project_root}")

    results = []

    print("\n--- 1. Virtual Environment Check ---")
    results.append(check_virtual_env())

    print("\n--- 2. Python Version Check ---")
    results.append(check_python_version())

    print("\n--- 3. pip Tooling Check ---")
    results.append(check_pip())

    print("\n--- 4. Dependency Installation Check ---")
    results.append(check_packages())

    print("\n--- 5. Environment Variables (.env) Check ---")
    results.append(check_env_loading(project_root))

    print("\n--- 6. Project Files & Directory Structure Check ---")
    results.append(check_directory_structure(project_root))

    print("\n--- 7. .gitignore Safety Check ---")
    results.append(check_gitignore_rules(project_root))

    print_header("Verification Summary")
    if all(results):
        print("ALL CHECKS PASSED: Environment is clean, isolated, and ready for development.")
        sys.exit(0)
    else:
        failed_count = results.count(False)
        print(f"VERIFICATION FAILED: {failed_count} check(s) failed. Please resolve the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
