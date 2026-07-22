# Renewable JWT Sessions

Jarvis uses short-lived access tokens and rotating refresh tokens for application
sessions. Google OAuth tokens are a separate integration concern.

## Token roles

- An access token authorizes protected API endpoints. It is a signed JWT with
  `type: "access"` and expires after `ACCESS_TOKEN_EXPIRE_MINUTES`.
- A refresh token creates a new token pair. It is a signed JWT with
  `type: "refresh"` and expires after `REFRESH_TOKEN_EXPIRE_DAYS`.
- The API never stores access tokens. Their expiration is the JWT `exp` claim.
- The API stores only an HMAC hash of each refresh token in
  `refresh_sessions`.

## Endpoints

### `POST /auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

A successful login revokes every active refresh session for that user and
creates one new active session. This is the current one-session-per-user MVP
policy.

### `POST /auth/refresh`

Request:

```json
{
  "refresh_token": "..."
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

The backend validates the JWT signature, JWT expiration, token type, stored
token hash, ownership, database expiration, and revocation state. It then
revokes the submitted refresh session and creates a new token pair in one
database transaction. Invalid refresh tokens return `401` with
`invalid_refresh_token`.

### `POST /auth/logout`

Request:

```json
{
  "refresh_token": "..."
}
```

Response: `204 No Content`.

Logout hashes the submitted refresh token and revokes its active session. It is
idempotent: an unknown, expired, or already revoked refresh token also returns
`204`. The client must delete both locally stored tokens after logout.

## Rotation behavior

```text
login
-> access_1 + refresh_1
-> hash(refresh_1) stored as an active session

refresh with refresh_1
-> revoke refresh_1 session
-> access_2 + refresh_2
-> hash(refresh_2) stored as an active session
```

Revoking a refresh token does not immediately invalidate access tokens already
issued. They remain valid only until their own `exp` claim, so the access-token
lifetime must remain short.

## Client behavior

Protected requests send:

```http
Authorization: Bearer <access_token>
```

When a protected request receives `401` because the access token has expired,
the Flutter HTTP client will call `/auth/refresh`, save the new pair, and retry
the original request once. If refresh fails, it clears the local session and
returns to login.

## Configuration

```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_SECRET_KEY=replace_with_a_long_random_secret
REFRESH_TOKEN_HASH_KEY=replace_with_a_different_long_random_secret
```

`REFRESH_TOKEN_HASH_KEY` is used only for HMAC hashing refresh tokens. It must
be different from `JWT_SECRET_KEY` and must never be committed.
