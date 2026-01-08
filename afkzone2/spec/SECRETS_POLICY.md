# Key Rotation & Secrets Hygiene Policy

## afkzone2/ Security Guidelines

### 1. Private Keys Storage

**Rule:** Private signing keys MUST NOT be stored in:
- Database
- Git repository
- Environment variable files committed to repo
- Plain text anywhere

**Approved storage:**
- GitHub Secrets (for CI/CD)
- HashiCorp Vault (production)
- AWS Secrets Manager / Azure Key Vault

### 2. Key Rotation Schedule

| Key Type | Rotation Frequency | Responsible Team |
|----------|-------------------|------------------|
| JWT signing key | Every 90 days | Backend |
| API tokens | Every 30 days | Ops |
| Signing certificates | Annually | Security |
| Admin passwords | Every 60 days | Admin |

### 3. Separation of Duties

| Operation | Requires |
|-----------|----------|
| Create production key | Security Lead + CTO approval |
| Deploy with new key | DevOps + Backend Lead |
| Rotate key | Security team with audit log |
| Access raw keys | Only CI/CD automation (no humans) |

### 4. CI/CD Secret Access

```yaml
# Correct way to access secrets in afkzone2-ci.yml
env:
  JWT_SECRET: ${{ secrets.AFKZONE2_JWT_SECRET }}
  SIGNING_KEY: ${{ secrets.AFKZONE2_SIGNING_KEY }}
```

**NEVER commit these to repo:**
- .env files with real secrets
- Private keys in any format
- API tokens

### 5. Audit Requirements

- All key access logged to CloudWatch/equivalent
- Key rotation triggers Slack notification
- Failed key operations alert on-call

---

## Checklist for New Keys

- [ ] Create key in secrets manager
- [ ] Add to CI/CD with `AFKZONE2_` prefix
- [ ] Document rotation schedule
- [ ] Assign owner
- [ ] Test rotation procedure
