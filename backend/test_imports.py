import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, '..')

# Test all imports one by one and catch errors
errors = []

try:
    from routes import health
except Exception as e:
    errors.append(f'health route: {e}')

try:
    from services import audit_runner
except Exception as e:
    errors.append(f'audit_runner service: {e}')

try:
    import veritas.config.settings
except Exception as e:
    errors.append(f'verititas.config.settings: {e}')

try:
    from veritas.db import get_db
except Exception as e:
    errors.append(f'verititas.db.get_db: {e}')

try:
    from veritas.db.models import Audit, AuditFinding, AuditScreenshot, AuditStatus
except Exception as e:
    errors.append(f'verititas.db.models: {e}')

try:
    from veritas.db.repositories import AuditRepository
except Exception as e:
    errors.append(f'verititas.db.repositories: {e}')

try:
    from veritas.screenshots.storage import ScreenshotStorage
except Exception as e:
    errors.append(f'verititas.screenshots.storage: {e}')

if errors:
    print('ERRORS FOUND:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
else:
    print('All imports successful!')
