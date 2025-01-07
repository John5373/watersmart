"""Main WaterSmart module"""

import aiohttp
import asyncio
import async_timeout
import logging
import socket
import time

from aiohttp_client_cache import CachedSession, SQLiteBackend
from importlib.metadata import version


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
        if session:
            self._session = session
        else:
            self._headers = {"User-Agent": "py-watersmart " + version("py-watersmart")}
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
        logging.debug("WatersmartClient ready, headers: %s", self._headers)

    async def _login(self):
        url = f"{self._url}/index.php/welcome/login?forceEmail=1"
        login = {"token": "", "email": self._email, "password": self._password}
        result = await self._session.post(url, data=login)
        logging.debug(result)

    async def _populate_data(self):
        url = f"{self._url}/index.php/rest/v1/Chart/RealTimeChart"
        chart_rsp = await self._session.get(url)
        if chart_rsp.status != 200:
            raise WatersmartClientAuthenticationError()
        data = await chart_rsp.json()
        self._data_series = data["data"]["series"]

    @classmethod
    def _amend_with_local_ts(cls, datapoint):
        # The read_datetime is a timestamp in local TZ, not UTC, which
        # confuses python datetime, so use the naive struct_time
        ts = time.gmtime(datapoint["read_datetime"])
        result = datapoint.copy()
        result["local_datetime"] = time.strftime("%Y-%m-%d %H:%M:%S", ts)
        return result

    async def usage(self):
        if not self._data_series:
            try:
                async with async_timeout.timeout(10):
                    logging.debug("Loading watersmart data from %s", self._url)
                    await self._login()
                    await self._populate_data()
            except WatersmartClientAuthenticationError as e:
                raise e
            except asyncio.TimeoutError as exception:
                raise WatersmartClientCommunicationError(
                    "Timeout error fetching information",
                ) from exception
            except (aiohttp.ClientError, socket.gaierror) as exception:
                raise WatersmartClientCommunicationError(
                    "Error fetching information",
                ) from exception
            except Exception as exception:  # pylint: disable=broad-except
                raise WatersmartClientError(
                    "Something really wrong happened!"
                ) from exception
            finally:
                await self._close()

        result = []
        for datapoint in self._data_series:
            result.append(WatersmartClient._amend_with_local_ts(datapoint))
        return result

    async def _close(self):
        await self._session.close()
