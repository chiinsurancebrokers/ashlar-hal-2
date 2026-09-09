# HAL v6.5 — Lead Routing + Gmail API

The applicant form remains unchanged. Only the delivery provider changes.

```text
Applicant
  -> HAL web form
  -> POST /api/v1/leads
  -> Railway backend
  -> Google OAuth access token
  -> Gmail API users.messages.send
  -> Ashlar inbox
```

## Gmail permission

HAL requests only:

`https://www.googleapis.com/auth/gmail.send`

It does not need inbox-read access.

## Railway variables

```text
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
GMAIL_SENDER_EMAIL
GMAIL_LEAD_RECIPIENT
```

- `GMAIL_SENDER_EMAIL`: the Gmail / Google Workspace mailbox authorised by OAuth.
- `GMAIL_LEAD_RECIPIENT`: the inbox that should receive HAL leads. It can be the same address or another Ashlar/CHI inbox.

No OAuth credentials are exposed to the browser.

## Email behaviour

HAL sets:

- `From`: authorised Gmail sender
- `To`: configured lead recipient
- `Reply-To`: applicant's email

So clicking Reply in Gmail addresses the response directly to the applicant.

## Refresh-token behaviour

HAL exchanges the refresh token for short-lived Google access tokens automatically.
The refresh token should be stored only in Railway Variables, never GitHub.
