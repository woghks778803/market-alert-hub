from html import unescape

from app.domain import NewsPort, NewsDTO
from app.infra.external.translation.google.rest_client import (
    GoogleTranslateTextRequest,
    GoogleTranslationRestClient,
)

class GoogleTranslation(NewsPort.GoogleTranslation):
    def __init__(
        self,
        *,
        rest_client: GoogleTranslationRestClient,
        max_batch_size: int = 50,
    ) -> None:
        self._rest_client = rest_client
        self._max_batch_size = max_batch_size

    def translate_batch(
        self,
        request: NewsDTO.TranslateBatchRequest,
    ) -> NewsDTO.TranslateBatchResult:
        results: list[NewsDTO.TranslatedTextItem] = []

        for chunk in self._chunk(request.items, self._max_batch_size):
            response = self._rest_client.translate_text(
                GoogleTranslateTextRequest(
                    source_language=request.source_language,
                    target_language=request.target_language,
                    texts=[item.text for item in chunk],
                )
            )

            if len(response.translated_texts) != len(chunk):
                raise RuntimeError("translation response count mismatch")

            # 같은 순서끼리 묶어서 하나씩 꺼내는 함수 (zip)
            for source_item, translated_text in zip(chunk, response.translated_texts): 
                results.append(
                    NewsDTO.TranslatedTextItem(
                        ref_id=source_item.ref_id,
                        original_text=source_item.text,
                        translated_text=unescape(translated_text),
                    )
                )

        return NewsDTO.TranslateBatchResult(items=results)

    def _chunk(
        self,
        items: list,
        size: int,
    ) -> list[list]:
        return [
            items[index:index + size]
            for index in range(0, len(items), size)
        ]