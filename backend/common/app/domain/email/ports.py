from typing import Protocol, Sequence, Mapping, Any

class EmailClient(Protocol):
    def send(
        self,
        subject: str,
        html_body: str,
        to: Sequence[str],
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: Sequence[str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict: ...
    
    # def send_template(
    #     self,
    #     template_name: str,
    #     template_data: Mapping[str, Any],
    #     to: Sequence[str],
    #     cc: Sequence[str] | None = None,
    #     bcc: Sequence[str] | None = None,
    #     reply_to: Sequence[str] | None = None,
    #     headers: Mapping[str, str] | None = None,
    #     subject_override: str | None = None,
    # ) -> str: ...

class EmailTemplateRenderer(Protocol):
    def render(self, template_name: str, context: Mapping[str, Any]) -> str: ...