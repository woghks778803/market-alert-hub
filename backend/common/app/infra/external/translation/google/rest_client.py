from dataclasses import dataclass

from app.infra.external.transport.impl.httpx import (
    HttpxTransport,
    HttpxTransportConfig,
)


@dataclass(frozen=True)
class GoogleTranslationRestClientConfig:
    api_key: str
    base_url: str
    timeout_sec: float = 10.0


@dataclass(frozen=True)
class GoogleTranslateTextRequest:
    source_language: str
    target_language: str
    texts: list[str]


@dataclass(frozen=True)
class GoogleTranslateTextResponse:
    translated_texts: list[str]


class GoogleTranslationRestClient:
    def __init__(self, config: GoogleTranslationRestClientConfig) -> None:
        if not config.base_url:
            raise RuntimeError("Google base_url is required")
            
        self._config = config

    def translate_text(
        self,
        request: GoogleTranslateTextRequest,
    ) -> GoogleTranslateTextResponse:
        transport = HttpxTransport(
            HttpxTransportConfig(
                base_url=self._config.base_url,
                timeout_sec=self._config.timeout_sec,
            )
        )

        try:
            response = transport.post(
                "/language/translate/v2",
                params={
                    "key": self._config.api_key,
                },
                json={
                    "q": request.texts,
                    "source": request.source_language,
                    "target": request.target_language,
                    "format": "text",
                },
            )
        finally:
            transport.close()

        status_code = getattr(response, "status_code", 0)
        if status_code < 200 or status_code >= 300:
            raise RuntimeError(f"google translation failed: status_code={status_code}")

        body = response.json()

        translations = body.get("data", {}).get("translations", [])
        translated_texts = [
            item.get("translatedText", "")
            for item in translations
        ]

        return GoogleTranslateTextResponse(
            translated_texts=translated_texts,
        )

def get_google_translation_rest_client(
    config: GoogleTranslationRestClientConfig
) -> GoogleTranslationRestClient:
    return GoogleTranslationRestClient(config)