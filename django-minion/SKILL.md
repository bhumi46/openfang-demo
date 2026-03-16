# Django Minion — Domain Knowledge
# Injected into agent context at every run

## COMMON DJANGO ERROR PATTERNS

### Test failures (confidence guide)

| Error pattern | Likely cause | Safe fix | Confidence |
|---|---|---|---|
| `AssertionError: X != Y` | Wrong expected value in test | Update assertion or fix logic | 75% |
| `django.db.utils.IntegrityError` | Missing required field / constraint | Add default or fix test fixture | 60% — check carefully |
| `ImportError: cannot import name X` | Renamed or moved symbol | Update import path | 90% |
| `AttributeError: 'NoneType' object` | Missing null check | Add `if obj is not None` guard | 85% |
| `django.core.exceptions.ImproperlyConfigured` | Missing setting or misconfigured app | Add missing setting in test settings | 80% |
| `django.test.utils.DatabaseBlockedError` | Transaction in test needing `@transaction.atomic` | Add decorator | 85% |
| `selenium.common.exceptions.NoSuchElementException` | UI test timing | Add explicit wait — skip if E2E | ESCALATE |

### Linting errors (confidence: 95%)

| Error | Fix |
|---|---|
| `E501 line too long` | Wrap with `\` or break string / call |
| `F401 imported but unused` | Remove import (check for `__all__` first) |
| `E302 expected 2 blank lines` | Add blank lines before class/function |
| `W291 trailing whitespace` | Remove trailing spaces |
| `I001 import order` | Run `isort {file}` |
| `E711 comparison to None` | Change `== None` to `is None` |

### Always escalate — do not attempt fix

- Any error containing: `migrations`, `IntegrityError` on real data, `FATAL`, `production`
- `OperationalError: no such table` → migration not run — escalate
- `PermissionDenied` in non-test context → auth config — escalate
- Any error in `settings/production.py` scope — escalate
- Test file is `test_integration_*` or `test_e2e_*` — escalate (infra scope)

---

## DJANGO PROJECT STRUCTURE REFERENCE

```
myapp/
├── models.py          # ORM models — edit carefully, avoid schema changes
├── views.py           # View logic — safe to edit
├── urls.py            # URL routing — safe to edit
├── serializers.py     # DRF serializers — safe to edit
├── forms.py           # Django forms — safe to edit
├── admin.py           # Admin config — safe to edit
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   └── test_forms.py
├── migrations/        # NEVER TOUCH
└── management/        # Management commands — safe to edit
```

---

## GITHUB API QUICK REFERENCE

```bash
# List failing CI runs
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/$GITHUB_REPO/actions/runs?status=failure&per_page=5"

# Get run logs (returns zip — extract text)
curl -sL -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/$GITHUB_REPO/actions/runs/{run_id}/logs"

# Open a pull request
curl -s -X POST -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/$GITHUB_REPO/pulls" \
  -d '{"title":"...","body":"...","head":"...","base":"main"}'

# Add labels to PR
curl -s -X POST -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/$GITHUB_REPO/issues/{pr_number}/labels" \
  -d '["minion-generated","needs-review"]'
```

---

## DJANGO TEST COMMANDS

```bash
# Run all tests
python -m pytest myapp/ -v --tb=short

# Run only a specific test file
python -m pytest myapp/tests/test_views.py -v

# Run with coverage
python -m pytest myapp/ --cov=myapp --cov-report=term-missing

# Django system check
python manage.py check

# Check for missing migrations (DO NOT run makemigrations — only check)
python manage.py migrate --check
```

---

## QUALITY GATES (check all before opening PR)

- [ ] `flake8` passes with 0 errors
- [ ] `black --check` passes
- [ ] `isort --check-only` passes
- [ ] `python manage.py check` shows 0 ERRORS (warnings OK)
- [ ] `pytest` — all existing tests pass (new failures = abandon)
- [ ] Diff does NOT touch `migrations/`, `.env`, `settings/production.py`
- [ ] Diff is under 8 files
- [ ] No secrets in diff: `git diff | grep -iE "secret|password|token|key"`
- [ ] Branch is based on latest `main`
- [ ] PR description is filled in with root cause + confidence score
