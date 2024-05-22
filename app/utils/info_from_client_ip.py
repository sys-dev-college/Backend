import ipaddress

import ipinfo

from app.config import settings

# handler = ipinfo.getHandlerAsync(settings.IPINFO_ACCESS_TOKEN)


class IPInfo:
    @staticmethod
    async def get_location(client_ip: str):
        # if ipaddress.ip_address(client_ip).is_private:
        return "41.8700,77.5900"

        # details = await handler.getDetails(ip_address=client_ip)
        # return details.loc
