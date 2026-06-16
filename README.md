# Deploying the RevOps Signal dashboard to Streamlit Community Cloud

This hosts [`revops_signal_dashboard.py`](revops_signal_dashboard.py) outside Snowflake so a
group of people can open one URL with **one shared password** — no per-user Snowflake
logins, no 2FA prompts.

**How auth works (two layers):**
- **People → app:** a single shared password (`APP_PASSWORD`).
- **App → Snowflake:** a read-only service account using **key-pair auth**, which is
  programmatic and never triggers MFA.

The same file still runs unchanged inside Snowflake — if `APP_PASSWORD` isn't set it skips
the password gate and uses the ambient Snowflake session.

---

## 1. Create the Snowflake service account + key pair

Run [`setup-revops-service-account.sql`](setup-revops-service-account.sql) in Snowsight as
ACCOUNTADMIN (or a role with `CREATE ROLE`/`CREATE USER`). It creates a read-only role
scoped to the `REVOPS_*` views only.

Generate the key pair locally:

```bash
# Encrypted private key (you'll be prompted for a passphrase)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8
# Public key — paste the body into the ALTER USER ... SET RSA_PUBLIC_KEY step in the SQL
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

Keep `rsa_key.p8` secret. Never commit it.

## 2. Push to GitHub

Make sure the repo contains `revops_signal_dashboard.py` and `requirements.txt`.
Do **not** commit `rsa_key.p8`, `.streamlit/secrets.toml`, or any password.

## 3. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io → **New app**.
2. Pick this repo/branch, main file path = `revops_signal_dashboard.py`.
3. Open **Advanced settings → Secrets** and paste (TOML):

```toml
APP_PASSWORD = "pick-a-strong-shared-password"

sf_account   = "youraccount-region"   # e.g. ab12345.us-east-1
sf_user       = "REVOPS_DASHBOARD_SVC"
sf_role       = "REVOPS_DASHBOARD_RO"
sf_warehouse  = "REVOPS_DASHBOARD_WH"
sf_database   = "GOLD_V3_DB"
sf_schema     = "SALES"

# Full PEM contents of rsa_key.p8, including BEGIN/END lines. Use triple quotes.
sf_private_key = """
-----BEGIN ENCRYPTED PRIVATE KEY-----
...
-----END ENCRYPTED PRIVATE KEY-----
"""
# Only if you set a passphrase when generating the key:
sf_private_key_passphrase = "your-key-passphrase"
```

4. Deploy. Share the URL + the shared password with your team.

## Security notes

- The shared password is the only thing between the public URL and your revenue data —
  make it strong and rotate it (just edit the secret) if it leaks.
- The service-account role is read-only on the `REVOPS_*` views only. It cannot write or
  read anything else, which limits the blast radius if the key is ever exposed.
- Rotate the key pair periodically: generate a new pair, `ALTER USER ... SET
  RSA_PUBLIC_KEY_2`, update the secret, then drop the old key.
