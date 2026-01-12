import json
import httpx
from dataclasses import dataclass

from .errors import UpbitHttpError, UpbitRateLimitError, UpbitDecodeError
from .types import UpbitMarket


@dataclass(frozen=True)
class UpbitRestClientConfig:
    base_url: str = "https://api.upbit.com"
    timeout_sec: float = 10.0


class UpbitRestClient:
    def __init__(self, config: UpbitRestClientConfig | None = None) -> None:
        self._config = config or UpbitRestClientConfig()
        self._client: httpx.Client | None = None

    def __enter__(self) -> "UpbitRestClient":
        self._ensure_client()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.Client(
            base_url=self._config.base_url,
            timeout=httpx.Timeout(self._config.timeout_sec),
        )

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None

    def _get_json(self, path: str, *, params: dict | None = None) -> object:
        self._ensure_client()
        assert self._client is not None

        resp = self._client.get(path, params=params)
        text = resp.text

        if resp.status_code == 429:
            raise UpbitRateLimitError(resp.status_code, "Upbit rate limited", body=text)
        if resp.status_code >= 400:
            raise UpbitHttpError(
                resp.status_code, f"Upbit http error: {resp.status_code}", body=text
            )

        try:
            return json.loads(text)
        except Exception as e:
            raise UpbitDecodeError(f"Failed to decode Upbit response: {e}") from e

    def list_markets(self) -> list[UpbitMarket]:
        """
        GET /v1/market/all
        - 실제 params는 필요 시 추가(예: isDetails=true)
        """
        data = self._get_json("/v1/market/all", params={"isDetails": "false"})
        if not isinstance(data, list):
            raise UpbitDecodeError("Unexpected markets payload shape")

        out: list[UpbitMarket] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            market = item.get("market")
            kname = item.get("korean_name")
            ename = item.get("english_name")
            if market and kname and ename:
                out.append(
                    UpbitMarket(market=market, korean_name=kname, english_name=ename)
                )
        return out

def get_rest_client(config: UpbitRestClientConfig) -> UpbitRestClient:
    return UpbitRestClient(config)