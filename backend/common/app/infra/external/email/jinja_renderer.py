from typing import Mapping, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateError
from app.domain import EmailPort, TemplateRenderError

TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "email"

class JinjaEmailRenderer(EmailPort.EmailTemplateRenderer):
    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=False,
            auto_reload=True,
        )

    def render(self, template_name: str, context: Mapping[str, Any]) -> str:
        try:
            tpl = self.env.get_template(template_name)
            return tpl.render(**context)
        except TemplateError as ex:
            raise TemplateRenderError(f"Failed to render template: {template_name}") from ex
