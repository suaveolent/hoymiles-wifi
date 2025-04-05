import asyncio
from hoymiles_wifi.dtu import DTU

async def main():
    dtu = DTU(host="192.168.1.184")
    response = await dtu.async_app_get_hist_power()
    print(response)

asyncio.run(main())