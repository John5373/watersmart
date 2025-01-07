import aiohttp
import asyncio
import async_timeout
import logging
import socket
import time
from aiohttp_client_cache import CachedSession, SQLiteBackend

class WatersmartClientError(Exception):
    """Exception to indicate a general API error."""


class WatersmartClientCommunicationError(WatersmartClientError):
    """Exception to indicate a communication error."""


class WatersmartClientAuthenticationError(WatersmartClientError):
    """Exception to indicate an authentication error."""


class WatersmartClient:
    def __init__(self, *, url, email, password, session=None):
        self._url = url
        self._email = email
        self._password = password
        self._data_series = []
        self._logger = logging.getLogger(__name__)

        if session:
            self._session = session
        else:
            self._headers = {"User-Agent": "watersmart/1.0"}
            self._cache = SQLiteBackend(
                expire_after=60 * 60 * 6,
                include_headers=False,
                cache_name="~/.cache/py-watersmart.db",
            )
            self._session = CachedSession(
                cache=self._cache,
                headers=self._headers,
            )
        assert "watersmart.com" in url, "Expected a watersmart.com URL"
        assert "http" in url, "Expected an http/https schema"
        self._logger.debug("WatersmartClient ready, headers: %s", self._headers)

    async def _login(self):
        url = f"{self._url}/index.php/welcome/login?forceEmail=1"
        login = {"token": "", "email": self._email, "password": self._password}

        self._logger.debug("Attempting login with email: %s", self._email)
        result = await self._session.post(url, data=login)
        if result.status != 200:
            self._logger.error("Login failed, status: %s", result.status)
            raise WatersmartClientAuthenticationError("Invalid login response")
        self._logger.debug("Login successful")

    async def _populate_data(self):
        url = f"{self._url}/index.php/rest/v1/Chart/RealTimeChart"
        self._logger.debug("Fetching real-time chart data from %s", url)
        chart_rsp = await self._session.get(url)
        if chart_rsp.status != 200:
            self._logger.error("Failed to fetch data, status: %s", chart_rsp.status)
            raise WatersmartClientAuthenticationError("Failed to fetch chart data")
        data = await chart_rsp.json()
        self._logger.debug("Raw chart data: %s", data)
        self._data_series = data.get("data", {}).get("series", [])

    @classmethod
    def _amend_with_local_ts(cls, datapoint):
        ts = time.gmtime(datapoint["read_datetime"])
        result = datapoint.copy()
        result["local_datetime"] = time.strftime("%Y-%m-%d %H:%M:%S", ts)
        return result

  async def usage(self):
        """Fetch water usage data."""
        if not self._data_series:
            try:
                async with async_timeout.timeout(10):
                    self._logger.debug("Loading watersmart data from %s", self._url)
                    await self._login()
                    await self._populate_data()
            except WatersmartClientAuthenticationError as e:
                self._logger.error("Authentication error: %s", e)
                raise
            except asyncio.TimeoutError as e:
                self._logger.error("Timeout error while fetching data: %s", e)
                raise WatersmartClientCommunicationError("Timeout error fetching information") from e
            except (aiohttp.ClientError, socket.gaierror) as e:
                self._logger.error("Network error while fetching data: %s", e)
                raise WatersmartClientCommunicationError("Error fetching information") from e
            except Exception as e:
                self._logger.error("Unexpected error: %s", e)
                raise WatersmartClientError("An unexpected error occurred!") from e
            finally:
                await self._close()

        self._logger.debug("Raw data series: %s", self._data_series)

        # Parse the data
        try:
            result = []
            for datapoint in self._data_series:
                parsed_datapoint = {
                    "name": f"Water Usage {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(datapoint['read_datetime']))}",
                    "value": datapoint["gallons"],
                    "unit": "gallons",
                    "read_datetime": datapoint["read_datetime"],
                }
                result.append(parsed_datapoint)
            self._logger.debug("Parsed data for sensors: %s", result)
            return result
        except KeyError as e:
            self._logger.error("Key error while parsing data: %s", e)
            raise WatersmartClientError("Data format error!") from e

    async def _close(self):
        self._logger.debug("Closing session")
        await self._session.close()
