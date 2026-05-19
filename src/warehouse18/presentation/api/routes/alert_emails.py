from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from warehouse18.infrastructure.email.smtp_mailer import (
    MailerConfigError,
    MailerSendError,
    SmtpMailer,
)

router = APIRouter(prefix="/alerts/email", tags=["alerts-email"])


class TestEmailIn(BaseModel):
    to: str | None = Field(
        default=None,
        description="Optional recipient. If empty, WAREHOUSE18_EMAIL_TO_ALERTS is used.",
    )
    subject: str = "Warehouse18 test email"
    message: str | None = None


class EmailSendOut(BaseModel):
    status: str
    sent_to: list[str]
    subject: str


@router.post("/test", response_model=EmailSendOut)
def send_test_email(body: TestEmailIn):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = body.message or (
        "This is a Warehouse18 test email.\n\n"
        f"Generated at: {now}\n\n"
        "If you received this, the email configuration is working."
    )

    try:
        recipients = SmtpMailer().send_text(
            subject=body.subject,
            body=message,
            to=body.to,
        )
    except MailerConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MailerSendError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"SMTP send failed: {exc}",
        ) from exc

    return EmailSendOut(
        status="sent",
        sent_to=recipients,
        subject=body.subject,
    )