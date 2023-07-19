async def _update_xcsrf(check_cookie):
    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": check_cookie}) as client:
        res = await client.post("https://accountsettings.roblox.com/v1/email", ssl=False)
        check_xcsrf = res.headers.get("x-csrf-token")
        if check_xcsrf is None:
            print("invalid cookie")
            exit()
        return check_xcsrf


async def get_user_id(check_cookie):
    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": check_cookie}) as client:
        res = await client.get("https://users.roblox.com/v1/users/authenticated", ssl=False)
        data = await res.json()
        userid = data.get('id')
        if userid is None:
            print("Couldn't scrape user id. Error:", data)
            exit()
        return str(userid)

async def print_stats(speed, item_id, checks):
    while True:
        os.system('cls')
        print(f"Speed: {speed}")
        print(f"Checking item: {item_id}")
        print(f"Checks: {checks}")
        await asyncio.sleep(1)
        
async def buy_item(check_cookie, check_xcsrf, limitinfo, userid):
    try:
        data = {
            "collectibleItemId": limitinfo.get('CollectibleItemId'),
            "expectedCurrency": 1,
            "expectedPrice": limitinfo.get('PriceInRobux'),
            "expectedPurchaserId": int(userid),
            "expectedPurchaserType": "User",
            "expectedSellerId": int(limitinfo.get("Creator")["CreatorTargetId"]),
            "expectedSellerType": "User",
            "idempotencyKey": str(uuid.uuid4()),
            "collectibleProductId": limitinfo.get('CollectibleProductId')
        }

        async with aiohttp.ClientSession() as client:                 
            response = await client.post(f"https://apis.roblox.com/marketplace-sales/v1/item/{limitinfo.get('CollectibleItemId')}/purchase-item",
                                         json=data,
                                         headers={"x-csrf-token": check_xcsrf},
                                         cookies={".ROBLOSECURITY": check_cookie})

            try:
                json_response = await response.json()
            except aiohttp.ContentTypeError as e:
                print("Error trying to decode JSON")
                print(e)

            print(response)
            print("------------------")
            print(json_response["errorMessage"])
            print("------------------")
    except:
        print("General Error")
        print("------------------")
        
async def _id_check(session, check_xcsrf, check_cookie, item_id):
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
            
async def items_snipe(check_cookie, check_xcsrf, item_ids, userid):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None)) as session:
        for item_id in item_ids:
            await _id_check(session, check_xcsrf, check_cookie, item_id)

async def start(check_cookie, check_xcsrf, item_ids, userid):
    await asyncio.gather(
        items_snipe(check_cookie, check_xcsrf, item_ids, userid),
        print_stats(0, item_ids, 0)
    )
    
async def main():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except:
        exit("Error trying to open config")

    check_cookie = config["acc"]
    item_ids = config["item"]

    check_xcsrf = await _update_xcsrf(check_cookie)
    userid = await get_user_id(check_cookie)
    await start(check_cookie, check_xcsrf, item_ids, userid)

asyncio.run(main())
