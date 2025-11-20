# Security Guidelines

## Critical: Never Commit These Files

### Environment Variables & Secrets
- ❌ `.env` files (contains API keys, passwords)
- ❌ `.env.local`, `.env.production`, `.env.development`
- ❌ `secrets.json`, `credentials.json`
- ❌ Private keys (`.pem`, `.key`, `.p12`, `.pfx`)
- ❌ AWS credentials (`.aws/config`, `.aws/credentials`)
- ❌ Google Cloud credentials (`.gcloud/`)

**Protected by .gitignore:** ✅ YES

### Database Files
- ❌ `*.db`, `*.sqlite`, `*.sqlite3` (can contain customer data)
- ❌ `conversations.db` (contains conversation history)
- ❌ `orders.db` (contains order data)

**Protected by .gitignore:** ✅ YES

### Sensitive Configuration Files
- ❌ OAuth tokens
- ❌ API keys
- ❌ Database connection strings with passwords

**Protected by .gitignore:** ✅ YES

---

## What IS Safe to Commit

✅ Source code (`.py` files)
✅ Configuration templates (`.env.example`)
✅ Documentation (`.md` files)
✅ Project configuration (`pyproject.toml`)
✅ Dependency lock file (`uv.lock`)
✅ `.gitignore` itself

---

## Best Practices

### 1. Use `.env.example` Template

Create ``.env.example` with placeholders:

```env
# .env.example (SAFE TO COMMIT)
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///conversations.db
DEBUG=false
```

Then copy to `.env` and fill with real values:

```bash
cp .env.example .env
# Edit .env with real values
```

### 2. Keep Secrets Out

❌ **NEVER** do this:
```python
API_KEY = "sk-1234567890abcdefghij"  # EXPOSED!
```

✅ **DO** this instead:
```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
```

### 3. Verify Before Committing

Before pushing to GitHub:

```bash
# Check what files will be committed
git status

# See exact file contents that will be added
git diff --cached

# Check if any secrets are in the staged changes
git diff --cached | grep -E "(password|key|secret|token|api)"
```

### 4. If You Accidentally Committed Secrets

**DO THIS IMMEDIATELY:**

```bash
# Remove file from git history (dangerous, use with care)
git rm --cached .env
git commit --amend -m "Remove .env from tracking"
git push origin master --force-with-lease

# Rotate the exposed keys/tokens in your services
# Example: Regenerate OpenAI API key
```

⚠️ **WARNING:** Use `--force-with-lease` instead of `-f` to avoid overwriting others' work.

---

## Protected Files List

Current `.gitignore` protects:

### Secrets & Keys
- `.env` files (all variations)
- PEM, KEY, P12, PFX files
- `credentials.json`, `oauth*.json`
- `.aws/`, `.gcloud/`

### Databases
- `*.db`, `*.sqlite`, `*.sqlite3`
- `conversations.db`
- `orders.db`
- SQLite temp files (`.sqlite-shm`, `.sqlite-wal`)

### Python Build Artifacts
- `__pycache__/`
- `*.egg-info/`
- `build/`, `dist/`
- `.pytest_cache/`, `.coverage/`

### IDE Files
- `.vscode/`, `.idea/`
- All editor swap/backup files

### OS Files
- `Thumbs.db`, `.DS_Store`
- Windows/Mac/Linux temp files

---

## GitHub Security Scanning

If you push secrets to GitHub:

1. GitHub will automatically detect common patterns (API keys, tokens)
2. You'll get notifications
3. You should:
   - Immediately rotate the exposed secret
   - Remove from history (see above)
   - Update `.gitignore`

**Tools to prevent accidental commits:**

```bash
# Install pre-commit hook
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
EOF

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Deployment Security

When deploying to production:

1. **Never use .env file directly**
   - Use environment variables
   - Use secrets management (AWS Secrets Manager, Azure Key Vault)
   - Use `.env` only for local development

2. **Database Security**
   - Don't commit database dumps
   - Use encrypted backups
   - Restrict database access

3. **API Keys**
   - Rotate keys regularly
   - Use different keys for dev/prod
   - Monitor key usage

---

## Current Status

✅ `.gitignore` is comprehensive and protects:
- All environment files
- All database files
- All credential/key files
- IDE and OS files
- Build artifacts and caches

**Your repository is SAFE from accidental secret commits.**

---

## Emergency Checklist

If you suspect a secret was committed:

- [ ] Verify what was exposed
- [ ] Immediately rotate the secret (e.g., regenerate API key)
- [ ] Remove from git history
- [ ] Force push (⚠️ only if you're alone)
- [ ] Notify other developers
- [ ] Update `.gitignore`
- [ ] Audit git logs for similar issues

```bash
# Find all commits that touched .env
git log --all --oneline -- .env

# Show file contents in a specific commit
git show commit_hash:.env
```

---

For more information, see:
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP: Secrets Management](https://owasp.org/www-community/Sensitive_Data_Exposure)
