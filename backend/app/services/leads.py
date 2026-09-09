from __future__ import annotations

import base64
import html
from datetime import datetime, timezone
from email.message import EmailMessage
from uuid import uuid4

import httpx

from backend.app.core.config import get_settings


def classify_journey(message: str, state: dict | None = None) -> str:
    """Deterministic first-pass journey router."""
    text=(message or "").lower()
    state=state or {}

    travel_terms=[
        "travel insurance","travel plan","trip insurance","holiday insurance",
        "single trip","annual multi trip","annual multi-trip","travelling for",
        "traveling for","vacation","business trip","ταξιδιωτικ","ταξίδι","ταξιδι",
        "διακοπές","διακοπες"
    ]
    local_terms=[
        "local insurance","local health","domestic insurance","greek health insurance",
        "ασφάλιση υγείας στην ελλάδα","ασφαλιση υγειας στην ελλαδα",
        "ελληνικό πρόγραμμα υγείας","ελληνικο προγραμμα υγειας",
        "τοπική ασφάλιση","τοπικη ασφαλιση","μόνο ελλάδα","μονο ελλαδα"
    ]
    ipmi_terms=[
        "international health","international medical","ipmi","global health",
        "worldwide cover","worldwide insurance","expat health","international insurance",
        "διεθνή ασφάλιση","διεθνη ασφαλιση","διεθνές πρόγραμμα","διεθνες προγραμμα",
        "treatment abroad","cover abroad","comprehensive","hnwi","affluent"
    ]

    if any(x in text for x in travel_terms):
        return "travel"
    if any(x in text for x in local_terms):
        return "local_review"
    if any(x in text for x in ipmi_terms):
        return "ipmi"

    if any([
        state.get("cross_border_treatment_required"),
        state.get("continuity_portability_required"),
        state.get("high_annual_limit_required"),
        state.get("home_country_treatment_required"),
        state.get("client_segment") in {"hnwi","affluent","international","expat"},
    ]):
        return "ipmi"

    return str(state.get("journey") or "undetermined")


def lead_intent(message: str) -> bool:
    text=(message or "").lower()
    terms=[
        "send me a quote","give me a quote","request a quote","get a quote",
        "i want to apply","i want to proceed","let's proceed","lets proceed",
        "contact me","call me","email me","send proposal","proposal please",
        "θέλω προσφορά","θελω προσφορα","στείλε μου προσφορά","στειλε μου προσφορα",
        "θέλω να προχωρήσω","θελω να προχωρησω","επικοινωνήστε","επικοινωνηστε",
        "να με καλέσετε","να με καλεσετε","αίτηση","αιτηση"
    ]
    return any(x in text for x in terms)


def journey_cta(journey: str, show: bool = False) -> dict:
    labels={
        "ipmi":"Request an international health proposal",
        "travel":"Request a travel insurance proposal",
        "local_review":"Request a local-vs-international review",
        "undetermined":"Request a proposal",
    }
    return {
        "show":bool(show),
        "journey":journey,
        "label":labels.get(journey,labels["undetermined"]),
    }


async def _gmail_access_token() -> str:
    settings=get_settings()
    required={
        "GMAIL_CLIENT_ID":settings.gmail_client_id,
        "GMAIL_CLIENT_SECRET":settings.gmail_client_secret,
        "GMAIL_REFRESH_TOKEN":settings.gmail_refresh_token,
    }
    missing=[key for key,value in required.items() if not value]
    if missing:
        raise RuntimeError("Gmail OAuth is not configured: " + ", ".join(missing))

    async with httpx.AsyncClient(timeout=30) as client:
        response=await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id":settings.gmail_client_id,
                "client_secret":settings.gmail_client_secret,
                "refresh_token":settings.gmail_refresh_token,
                "grant_type":"refresh_token",
            },
        )

    if response.status_code < 200 or response.status_code >= 300:
        detail=(response.text or "OAuth token refresh failed")[:300]
        raise RuntimeError(f"Google OAuth returned {response.status_code}: {detail}")

    token=response.json().get("access_token")
    if not token:
        raise RuntimeError("Google OAuth did not return an access token.")
    return str(token)


def _safe(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _subject(interest: str, residence: str, age: str, reference: str) -> str:
    parts=["New HAL Lead", (interest or "Insurance Enquiry").strip()]
    if residence:
        parts.append(residence.strip())
    if age:
        parts.append(f"Age {age.strip()}")
    parts.append(reference)
    return " — ".join(parts)[:240]


def _build_message(payload: dict, reference: str, sender: str, recipient: str) -> EmailMessage:
    submitted=datetime.now(timezone.utc).isoformat()
    applicant_name=" ".join(
        x for x in [payload.get("first_name","").strip(),payload.get("last_name","").strip()] if x
    ).strip()

    plain=f"""New HAL insurance enquiry

Reference: {reference}
Submitted: {submitted}

INSURANCE INTEREST
{payload.get('insurance_interest','')}

APPLICANT
Name: {applicant_name}
Email: {payload.get('email','')}
Phone: {payload.get('phone','')}
Residence: {payload.get('residence_country','')}
Nationality: {payload.get('nationality','')}
Age: {payload.get('age','')}
Preferred contact: {payload.get('preferred_contact','')}

REQUEST
Coverage area / destination: {payload.get('coverage_area','')}
Family / travellers: {payload.get('family_members','')}
Approx. budget: {payload.get('budget','')}

Applicant note:
{payload.get('message','')}

HAL STRUCTURED STATE
{payload.get('hal_applicant_state','')}

HAL QUOTES DISCUSSED
{payload.get('hal_quotes','')}

RECENT HAL CONVERSATION
{payload.get('hal_conversation','')}

Consent recorded: {'Yes' if payload.get('consent') else 'No'}
"""

    html_body=f"""
    <html><body style="font-family:Arial,sans-serif;color:#172333;line-height:1.5">
      <h2 style="margin-bottom:4px">New HAL insurance enquiry</h2>
      <p style="color:#687586;margin-top:0">Reference: <strong>{_safe(reference)}</strong></p>

      <h3>Insurance interest</h3>
      <p>{_safe(payload.get('insurance_interest',''))}</p>

      <h3>Applicant</h3>
      <table cellpadding="5" cellspacing="0">
        <tr><td><strong>Name</strong></td><td>{_safe(applicant_name)}</td></tr>
        <tr><td><strong>Email</strong></td><td>{_safe(payload.get('email',''))}</td></tr>
        <tr><td><strong>Phone</strong></td><td>{_safe(payload.get('phone',''))}</td></tr>
        <tr><td><strong>Residence</strong></td><td>{_safe(payload.get('residence_country',''))}</td></tr>
        <tr><td><strong>Nationality</strong></td><td>{_safe(payload.get('nationality',''))}</td></tr>
        <tr><td><strong>Age</strong></td><td>{_safe(payload.get('age',''))}</td></tr>
        <tr><td><strong>Preferred contact</strong></td><td>{_safe(payload.get('preferred_contact',''))}</td></tr>
      </table>

      <h3>Request</h3>
      <p><strong>Coverage / destination:</strong> {_safe(payload.get('coverage_area',''))}<br>
      <strong>Family / travellers:</strong> {_safe(payload.get('family_members',''))}<br>
      <strong>Approx. budget:</strong> {_safe(payload.get('budget',''))}</p>

      <h3>Applicant note</h3>
      <p>{_safe(payload.get('message','')).replace(chr(10),'<br>')}</p>

      <h3>HAL structured state</h3>
      <pre style="white-space:pre-wrap;background:#f5f7f9;padding:12px;border-radius:8px">{_safe(payload.get('hal_applicant_state',''))}</pre>

      <h3>HAL quotes discussed</h3>
      <pre style="white-space:pre-wrap;background:#f5f7f9;padding:12px;border-radius:8px">{_safe(payload.get('hal_quotes',''))}</pre>

      <h3>Recent HAL conversation</h3>
      <pre style="white-space:pre-wrap;background:#f5f7f9;padding:12px;border-radius:8px">{_safe(payload.get('hal_conversation',''))}</pre>

      <p style="font-size:12px;color:#687586">Consent recorded: {'Yes' if payload.get('consent') else 'No'} · Submitted {submitted}</p>
    </body></html>
    """

    msg=EmailMessage()
    msg["From"]=sender
    msg["To"]=recipient
    msg["Subject"]=_subject(
        payload.get("insurance_interest",""),
        payload.get("residence_country",""),
        payload.get("age",""),
        reference,
    )
    if payload.get("email"):
        msg["Reply-To"]=payload["email"].strip()
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")
    return msg


async def send_gmail_lead(payload: dict) -> dict:
    settings=get_settings()

    if not settings.gmail_sender_email:
        raise RuntimeError("GMAIL_SENDER_EMAIL is not configured.")
    if not settings.gmail_lead_recipient:
        raise RuntimeError("GMAIL_LEAD_RECIPIENT is not configured.")

    reference=f"HAL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
    token=await _gmail_access_token()

    msg=_build_message(
        payload=payload,
        reference=reference,
        sender=settings.gmail_sender_email,
        recipient=settings.gmail_lead_recipient,
    )
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

    async with httpx.AsyncClient(timeout=30) as client:
        response=await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization":f"Bearer {token}",
                "Content-Type":"application/json",
            },
            json={"raw":raw},
        )

    if response.status_code < 200 or response.status_code >= 300:
        detail=(response.text or "Gmail delivery failed")[:400]
        raise RuntimeError(f"Gmail API returned {response.status_code}: {detail}")

    result=response.json()
    return {
        "status":"sent",
        "reference":reference,
        "gmail_message_id":result.get("id"),
    }



def _comparison_subject(name: str) -> str:
    return f"Your Ashlar international health insurance comparison{(' — ' + name) if name else ''}"[:240]


def _build_comparison_message(name: str, email: str, plans: list[dict], sender: str, broker_copy: str | None = None) -> EmailMessage:
    top=plans[0] if plans else {}
    rows=[]
    for p in plans:
        annual=float(p.get("premium") or 0)
        monthly=float(p.get("monthly") or annual/12 if annual else 0)
        badges=", ".join(p.get("fit_badges") or [])
        rows.append(f"""<tr>
          <td style='padding:12px;border-bottom:1px solid #e7ebef'><strong>{_safe(p.get('product_name'))}</strong><br><span style='color:#6b7786'>{_safe(p.get('insurer'))}</span></td>
          <td style='padding:12px;border-bottom:1px solid #e7ebef'>{_safe(p.get('currency','EUR'))} {annual:,.2f}<br><span style='color:#6b7786'>{_safe(p.get('currency','EUR'))} {monthly:,.2f}/month</span></td>
          <td style='padding:12px;border-bottom:1px solid #e7ebef'>{_safe(p.get('card_annual_limit'))}</td>
          <td style='padding:12px;border-bottom:1px solid #e7ebef'>{_safe(p.get('card_why'))}<br><span style='color:#6654d9'>{_safe(badges)}</span></td>
        </tr>""")
    plain_lines=["Your Ashlar health insurance comparison",""]
    for i,p in enumerate(plans,1):
        plain_lines += [
            f"{i}. {p.get('product_name')} — {p.get('insurer')}",
            f"Annual premium: {p.get('currency','EUR')} {float(p.get('premium') or 0):,.2f}",
            f"Annual limit: {p.get('card_annual_limit','')}",
            f"Why it may fit: {p.get('card_why','')}",""
        ]
    plain_lines.append("An Ashlar broker can review the wording, underwriting and final terms before you proceed.")

    html_body=f"""<html><body style='font-family:Arial,sans-serif;color:#162537;line-height:1.5'>
    <div style='max-width:760px;margin:auto'>
      <div style='font-size:13px;letter-spacing:.14em;font-weight:700;color:#0c1727'>ASHLAR ASSURANCE</div>
      <h1 style='font-size:28px;margin:14px 0 8px'>Your health insurance comparison</h1>
      <p style='color:#697789'>Dear {_safe(name) if name else 'Client'},</p>
      <p>Following your HAL session, here is the shortlist you asked us to send you.</p>
      {f"<p style='background:#f3f0ff;border-radius:12px;padding:14px'><strong>HAL's current top option:</strong> {_safe(top.get('product_name'))} — {_safe(top.get('insurer'))}</p>" if top else ''}
      <table style='border-collapse:collapse;width:100%;font-size:13px;margin:20px 0'>
        <thead><tr style='background:#f5f7f9'><th align='left' style='padding:12px'>Plan</th><th align='left'>Premium</th><th align='left'>Annual limit</th><th align='left'>Why it may fit</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      <p style='font-size:12px;color:#697789'>This is an indicative comparison, not confirmation of cover. Final premiums, eligibility, underwriting and policy terms remain subject to insurer confirmation.</p>
      <p>Kind regards,<br><strong>Ashlar Assurance</strong></p>
    </div></body></html>"""
    msg=EmailMessage()
    msg["From"]=sender
    msg["To"]=email
    if broker_copy and broker_copy.lower()!=email.lower():
        msg["Bcc"]=broker_copy
    msg["Subject"]=_comparison_subject(name)
    msg.set_content("\n".join(plain_lines))
    msg.add_alternative(html_body,subtype="html")
    return msg


async def send_gmail_comparison(name: str, email: str, plans: list[dict]) -> dict:
    settings=get_settings()
    if not settings.gmail_sender_email:
        raise RuntimeError("GMAIL_SENDER_EMAIL is not configured.")
    token=await _gmail_access_token()
    msg=_build_comparison_message(name,email,plans,settings.gmail_sender_email,settings.gmail_lead_recipient)
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    async with httpx.AsyncClient(timeout=30) as client:
        response=await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
            json={"raw":raw},
        )
    if response.status_code < 200 or response.status_code >= 300:
        detail=(response.text or "Gmail comparison delivery failed")[:400]
        raise RuntimeError(f"Gmail API returned {response.status_code}: {detail}")
    result=response.json()
    return {"status":"sent","gmail_message_id":result.get("id")}
