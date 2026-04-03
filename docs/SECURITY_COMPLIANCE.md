# Security Compliance — Panther Cloud Air
**Reference:** Announcements from Panther Cloud Air (Feb 11 & Mar 2, 2026)

---

## 1. Input Validation & Safe Database Access

- **Parameterized SQL:** All queries use `cursor.execute(sql, (params,))` — no f-strings or `.format()` in SQL
- **IATA codes:** Validated with `^[A-Z]{3}$` regex
- **Dates:** Validated with `^\d{4}-\d{2}-\d{2}$` regex
- **Required fields:** All endpoints return 400 if missing
- **DB constraints:** Foreign keys, UNIQUE, ENUM enforced at schema level

## 2. Authentication & Authorization

- **Password hashing:** bcrypt (exceeds SHA-512 requirement — adaptive, salted, OWASP-recommended)
- **Passwords never stored in plaintext** — only bcrypt hashes; never returned in API responses
- **Roles:** `user` and `admin`, enforced server-side via `@token_required` / `@role_required` decorators
- **JWT:** HS256, 8-hour expiry, rejects expired/tampered/missing tokens
- **Rate limiting:** Max 10 login attempts/min per IP
- **Account lockout:** After 5 failed attempts, `locked_at` timestamp set

## 3. Container & Configuration Security

- **DB not exposed:** No `ports:` mapping on `db` service — only reachable within `pca_network`
- **Least privilege:** Backend connects as `pca_user` (not root), runs as non-root `pca` user in container
- **Secrets in env vars:** JWT secret, DB password, admin password all via `os.getenv()` with `.env` file (not committed)
