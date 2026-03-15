#!/usr/bin/env python3
"""Test Validation Script - Checks syntax without running tests"""
import ast
import sys
from pathlib import Path


def validate_python_syntax(file_path):
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)


def main():
    """Main validation function"""
    test_files = [
        'tests/test_api_integrations.py',
        'tests/test_api_ai.py',
        'tests/test_api_celery.py',
        'tests/conftest.py',
    ]

    errors = []
    for test_file in test_files:
        path = Path(test_file)
        if path.exists():
            valid, error = validate_python_syntax(path)
            if not valid:
                errors.append(f"{test_file}: {error}")
                print(f"❌ {test_file}: {error}")
            else:
                print(f"✅ {test_file}: Valid syntax")
        else:
            print(f"⚠️  {test_file}: Not found")

    # Check app structure
    app_files = [
        'app/main.py',
        'app/api/celery.py',
        'app/api/integrations.py',
        'app/api/ai.py',
    ]

    for app_file in app_files:
        path = Path(app_file)
        if path.exists():
            valid, error = validate_python_syntax(path)
            if not valid:
                errors.append(f"{app_file}: {error}")
                print(f"❌ {app_file}: {error}")
            else:
                print(f"✅ {app_file}: Valid syntax")
        else:
            print(f"⚠️  {app_file}: Not found")

    if errors:
        print(f"\n❌ {len(errors)} error(s) found")
        return 1
    else:
        print(f"\n✅ All files validated successfully")
        return 0


if __name__ == '__main__':
    sys.exit(main())
