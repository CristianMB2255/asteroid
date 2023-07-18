import asyncio
import httpx
import json
import time
import uuid
import aiohttp
import os
import socketio

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except:
    exit("error trying to open config")
    
check_cookie = config["acc"]
item_id = config["item"]
speed = 0
checks = 0
    
async def print_stats():
    while True:
        os.system('cls')
        print(f"Speed: {speed}")
        print(f"Checking item: {item_id}")
        print(f"Checks: {checks}")
        await asyncio.sleep(1)
        
async def buy_item(session, limitinfo) -> None:
    try:
        data = {
            "collectibleItemId": limitinfo.get('CollectibleItemId'),
            "expectedCurrency": 1,
            "expectedPrice": limitinfo.get('PriceInRobux'),
            "expectedPurchaserId": int(userid),
            "expectedPurchaserType": "User",
            "expectedSellerId": int(limitinfo.get("Creator")["CreatorTargetId"]),
            "expectedSellerType": "User",
            "idempotencyKey": "random uuid4 string that will be your key or smthn",
            "collectibleProductId": limitinfo.get('CollectibleProductId')
        }

        async with aiohttp.ClientSession() as client:                 
            data["idempotencyKey"] = str(uuid.uuid4())
            response = await client.post(f"https://apis.roblox.com/marketplace-sales/v1/item/{limitinfo.get('CollectibleItemId')}/purchase-item",
                           json=data,
                           headers={"x-csrf-token": check_xcsrf},
                           cookies={".ROBLOSECURITY": check_cookie})


            try:
                  json_response = await response.json()
            except aiohttp.ContentTypeError as e:
                  print("Error trying to decode JSON")
            print(response)
            print("------------------")
            print(json_response["errorMessage"])
            print("------------------")
    except:
        print("General Error")
        print("------------------")
    
async def get_xcsrf(cookieD) -> str:
    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": cookieD}) as client:
        res = await client.post("https://accountsettings.roblox.com/v1/email", ssl=False)
        xcsrf_token = res.headers.get("x-csrf-token")
        if xcsrf_token is None:
            print("invalid cookie")
            exit(1)
        return xcsrf_token

async def _update_xcsrf():
    global check_xcsrf
    try:
        check_xcsrf = await get_xcsrf(check_cookie)
        return True
    except:
        return False

async def get_user_id():
    global userid
    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": check_cookie}) as client:
        res = await client.get("https://users.roblox.com/v1/users/authenticated", ssl=False)
        data = await res.json()
        userid = data.get('id')
        if userid is None:
            print("Couldn't scrape user id. Error:", data)
            exit(1)
        return userid
        
async def _id_check(session, item_id):
    global speed, checks
    t0 = asyncio.get_event_loop().time()
    url = f"https://economy.roblox.com/v2/assets/{item_id}/details"

    async with session.get(url,
                            headers={"x-csrf-token": check_xcsrf,
                                    'Accept': "application/json",
                                    'Accept-Encoding': 'gzip, deflate'},
                            cookies={".ROBLOSECURITY": check_cookie}, ssl=False) as res:
        response_text = await res.text()
        data = json.loads(response_text)
        if data.get("IsForSale") and data.get('CollectibleProductId') is not None:
            for i in range(4):
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None)) as session:
                    await buy_item(session, data)

            exit()

    speed = round(asyncio.get_event_loop().time() - t0, 2)
    checks += 1
            
async def items_snipe(item_id) -> None:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None)) as session:
        while 1:
            if len(item_id) > 0:
                    for ids in item_id:
                        await _id_check(session, int(ids))

async def start():
    await asyncio.gather(
        items_snipe(item_id),
        print_stats()
        )
    
asyncio.run(_update_xcsrf())
asyncio.run(get_user_id())
asyncio.run(start())
