from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests

from dashboard.config import (
    API_BASE_URL,
    API_TIMEOUT_SECONDS,
    DETECTION_INGEST_ENDPOINT,
    HEALTH_ENDPOINT,
)


logger = logging.getLogger(
    __name__
)


class FireCoreAPIClient:
    """
    HTTP client for Fire Intelligence Core.
    """

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: float = API_TIMEOUT_SECONDS,
    ) -> None:

        self.base_url = (
            base_url.rstrip("/")
        )

        self.timeout = timeout

        self.session = (
            requests.Session()
        )

    @property
    def detection_url(
        self,
    ) -> str:

        return (
            f"{self.base_url}"
            f"{DETECTION_INGEST_ENDPOINT}"
        )

    @property
    def health_url(
        self,
    ) -> str:

        return (
            f"{self.base_url}"
            f"{HEALTH_ENDPOINT}"
        )

    def check_health(
        self,
    ) -> Dict[str, Any]:

        start_time = (
            time.perf_counter()
        )

        try:

            response = self.session.get(
                self.health_url,
                timeout=self.timeout,
            )

            latency_ms = (
                time.perf_counter()
                - start_time
            ) * 1000.0

            response_data = {}

            if response.content:

                try:

                    response_data = (
                        response.json()
                    )

                except ValueError:

                    response_data = {
                        "raw_response": (
                            response.text
                        )
                    }

            return {
                "online": (
                    response.ok
                ),
                "status_code": (
                    response.status_code
                ),
                "latency_ms": (
                    latency_ms
                ),
                "data": (
                    response_data
                ),
                "error": (
                    None
                    if response.ok
                    else response_data
                ),
            }

        except requests.RequestException as exception:

            latency_ms = (
                time.perf_counter()
                - start_time
            ) * 1000.0

            logger.warning(
                "Health check failed: %s",
                exception,
            )

            return {
                "online": False,
                "status_code": None,
                "latency_ms": (
                    latency_ms
                ),
                "data": {},
                "error": str(
                    exception
                ),
            }

    def ingest_detection(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

        start_time = (
            time.perf_counter()
        )

        try:

            response = self.session.post(
                self.detection_url,
                json=payload,
                timeout=self.timeout,
            )

            latency_ms = (
                time.perf_counter()
                - start_time
            ) * 1000.0

            try:

                response_data = (
                    response.json()
                )

            except ValueError:

                response_data = {
                    "raw_response": (
                        response.text
                    )
                }

            if not response.ok:

                logger.warning(
                    (
                        "Detection request failed "
                        "status=%s response=%s"
                    ),
                    response.status_code,
                    response_data,
                )

            return {
                "success": (
                    response.ok
                ),
                "status_code": (
                    response.status_code
                ),
                "latency_ms": (
                    latency_ms
                ),
                "data": (
                    response_data
                ),
                "error": (
                    None
                    if response.ok
                    else response_data
                ),
            }

        except requests.RequestException as exception:

            latency_ms = (
                time.perf_counter()
                - start_time
            ) * 1000.0

            logger.exception(
                "Detection ingest failed."
            )

            return {
                "success": False,
                "status_code": None,
                "latency_ms": (
                    latency_ms
                ),
                "data": {},
                "error": str(
                    exception
                ),
            }


_default_client: Optional[
    FireCoreAPIClient
] = None


def get_api_client(
) -> FireCoreAPIClient:

    global _default_client

    if _default_client is None:

        _default_client = (
            FireCoreAPIClient()
        )

    return _default_client