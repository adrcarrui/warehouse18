from __future__ import annotations

import smtplib
from email.message import EmailMessage

from warehouse18.config import settings


class MailerConfigError(RuntimeError):
    pass


class MailerSendError(RuntimeError):
    pass


def _split_recipients(value: str | None) -> list[str]:
    if not value:
        return []

    normalized = value.replace(";", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


class SmtpMailer:
    def __init__(self) -> None:
        self.enabled = settings.email_enabled
        self.host = settings.email_smtp_host
        self.port = settings.email_smtp_port
        self.user = settings.email_smtp_user
        self.password = settings.email_smtp_password
        self.sender = settings.email_from
        self.default_recipients = settings.email_to_alerts
        self.use_tls = settings.email_use_tls
        self.use_ssl = settings.email_use_ssl
        self.timeout_seconds = settings.email_timeout_seconds

        print("EMAIL DEBUG enabled:", repr(self.enabled))
        print("EMAIL DEBUG host:", repr(self.host))
        print("EMAIL DEBUG port:", repr(self.port))
        print("EMAIL DEBUG user:", repr(self.user))
        print("EMAIL DEBUG from:", repr(self.sender))
        print("EMAIL DEBUG tls:", repr(self.use_tls))
        print("EMAIL DEBUG ssl:", repr(self.use_ssl))

    def _validate_config(self, recipients: list[str]) -> None:
        if not self.enabled:
            raise MailerConfigError(
                "Email sending is disabled. Set WAREHOUSE18_EMAIL_ENABLED=true."
            )

        if not self.host:
            raise MailerConfigError(
                "Missing SMTP host. Set WAREHOUSE18_EMAIL_SMTP_HOST."
            )

        if not self.sender:
            raise MailerConfigError(
                "Missing sender email. Set WAREHOUSE18_EMAIL_FROM."
            )

        if not recipients:
            raise MailerConfigError(
                "Missing recipients. Set WAREHOUSE18_EMAIL_TO_ALERTS or pass a recipient."
            )

    def send_text(
        self,
        *,
        subject: str,
        body: str,
        to: str | list[str] | None = None,
    ) -> list[str]:
        if isinstance(to, list):
            recipients = to
        else:
            recipients = _split_recipients(to) or _split_recipients(self.default_recipients)

        self._validate_config(recipients)

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body)

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout_seconds,
                ) as smtp:
                    self._login_if_needed(smtp)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(
                    self.host,
                    self.port,
                    timeout=self.timeout_seconds,
                ) as smtp:
                    smtp.ehlo()

                    if self.use_tls:
                        smtp.starttls()
                        smtp.ehlo()

                    self._login_if_needed(smtp)
                    smtp.send_message(message)

        except smtplib.SMTPException as exc:
            raise MailerSendError(str(exc)) from exc
        except OSError as exc:
            raise MailerSendError(str(exc)) from exc

        return recipients

    def _login_if_needed(self, smtp: smtplib.SMTP) -> None:
        if self.user:
            smtp.login(self.user, self.password)