from typing import Sequence, Mapping
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from app.domain import EmailPort, EmailSendError
from app.core.settings import settings


class SesEmailClient(EmailPort.EmailClient):
    def __init__(self) -> None:
        cfg = BotoConfig(
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=3,
            read_timeout=5,
        )
        session = (
            boto3.session.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY
            else boto3.session.Session(region_name=settings.AWS_REGION)
        )
        self.client = session.client("sesv2", config=cfg)
        self.from_email = settings.SES_FROM_EMAIL
        self.configuration_set = settings.SES_CONFIGURATION_SET

    def send(
        self,
        subject: str,
        html_body: str,
        to: Sequence[str],
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: Sequence[str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        try:
            kwargs = {
                "FromEmailAddress": self.from_email,
                "Destination": {
                    "ToAddresses": list(to),
                    "CcAddresses": list(cc or []),
                    "BccAddresses": list(bcc or []),
                },
                "Content": {
                    "Simple": {
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
                    }
                },
            }
            if reply_to:
                kwargs["ReplyToAddresses"] = list(reply_to)
            if headers:
                kwargs["EmailTags"] = [
                    {"Name": k, "Value": v} for k, v in headers.items()
                ]
            if self.configuration_set:
                kwargs["ConfigurationSetName"] = self.configuration_set

            res = self.client.send_email(**kwargs)
            return res.get("MessageId", "")
        except ClientError as ex:
            code = ex.response.get("Error", {}).get("Code", "unknown")
            raise EmailSendError(f"SES send_email failed: {code}") from ex
