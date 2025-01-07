# Modify py-watersmart Library for Asynchronous Use
# File: watersmart.py (modified)

import aiohttp
import asyncio

class WaterSmart:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = None
        self.base_url = "https://api.watersmart.com"

    async def _authenticate(self):
        """Authenticate with the WaterSmart API."""
        async with aiohttp.ClientSession() as session:
            self.session = session
            url = f"{self.base_url}/login"
            payload = {"username": self.username, "password": self.password}
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("token")
                else:
                    raise Exception(f"Failed to authenticate: {response.status}")

    async def get_usage(self):
        """Fetch water usage data."""
        if not self.session:
            await self._authenticate()

        url = f"{self.base_url}/usage"
        headers = {"Authorization": f"Bearer {self.token}"}
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to fetch usage data: {response.status}")

    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
