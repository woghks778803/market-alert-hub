from typing import Sequence, Mapping
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from app.domain import EmailPort, EmailSendError
from app.runtime.settings import settings


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
    ) -> dict:
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

            # res = self.client.send_email(**kwargs)
            # {'ResponseMetadata': {'RequestId': 'f8bb7ab3-2578-4ce2-a632-2ab80f0858f4', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Mon, 15 Dec 2025 06:56:15 GMT', 'content-type': 'application/json', 'content-length': '76', 'connection': 'keep-alive', 'x-amzn-requestid': 'f8bb7ab3-2578-4ce2-a632-2ab80f0858f4'}, 'RetryAttempts': 0}, 'MessageId': '010c019b20cba5c1-b201a0a0-5f10-443b-a696-cdab0a1fec66-000000'}
            # return res.get("MessageId", "")
            return self.client.send_email(**kwargs)
        except ClientError as ex:
            code = ex.response.get("Error", {}).get("Code", "unknown")
            raise EmailSendError(f"SES send_email failed: {code}") from ex
