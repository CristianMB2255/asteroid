try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except:
    exit("error trying to open config")

check_cookie = config["acc"]
item_ids = config["item"]
speed = 0
checks = 0
bought = 0

async def print_stats():
    while True:
        os.system('cls')
        print(f"Speed: {speed}")
        print(f"Checking item: {item_ids}")
        print(f"Checks: {checks}")
        print(f"Bought: {bought}")
        await asyncio.sleep(1)

async def get_xcsrf(cookie) -> str:
    global check_xcsrf
    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": cookie}) as client:
        res = await client.post("https://accountsettings.roblox.com/v1/email", ssl=False)
        check_xcsrf = res.headers.get("x-csrf-token")
        if check_xcsrf is None:
            print("Invalid cookie")
            exit(1)
        return check_xcsrf

async def get_user_id(cookie) -> str:
    global userid
    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": cookie}) as client:
        res = await client.get("https://users.roblox.com/v1/users/authenticated", ssl=False)
        data = await res.json()
        userid = data.get('id')
        if userid is None:
            print("Couldn't scrape user id. Error:", data)
            exit(1)
        return userid

async def buy_item(session, data) -> None:   
    global bought
    try:
        async with session.post(f"https://apis.roblox.com/marketplace-sales/v1/item/{data['collectibleItemId']}/purchase-item",
                           json=data,
                           headers={"x-csrf-token": check_xcsrf},
                           cookies={".ROBLOSECURITY": check_cookie}) as res:

            try:
                  json_response = await res.json()
            except aiohttp.ContentTypeError as e:
                  print("Error trying to decode JSON")
            print("------------------")
            print(json_response["errorMessage"])
            print("------------------")
            if(json_response["purchased"] == True):
                bought += 1
    except:
        print("General Error")
        print("------------------")
        
async def _id_check(session, item_id):
    global speed, checks
    t0 = asyncio.get_event_loop().time()
    url = f"https://economy.roblox.com/v2/assets/{item_id}/details"

    async with session.get(
        url,
        headers={"x-csrf-token": check_xcsrf, 'Accept': "application/json", 'Accept-Encoding': 'gzip, deflate'},
        cookies={".ROBLOSECURITY": check_cookie},
        ssl=False
    ) as res:
        response_text = await res.text()
        item_stats = json.loads(response_text)
        if item_stats.get("IsForSale") and item_stats.get('CollectibleProductId') is not None and item_stats.get('Remaining') > 0:
            data = {
            "collectibleItemId": item_stats.get('CollectibleItemId'),
            "expectedCurrency": 1,
            "expectedPrice": item_stats.get('PriceInRobux'),
            "expectedPurchaserId": int(userid),
            "expectedPurchaserType": "User",
            "expectedSellerId": int(item_stats.get("Creator")["CreatorTargetId"]),
            "expectedSellerType": "User",
            "idempotencyKey": str(uuid.uuid4()),
            "collectibleProductId": item_stats.get('CollectibleProductId')
            }
            
            for i in range(4):
                await buy_item(session, data)
                time.await(0.5)

        elif item_stats.get('Remaining') == 0:
            config['item'].remove(item_id)
            with open("config.json", "w") as file:
                json.dump(config, file, indent=1)

    speed = round(asyncio.get_event_loop().time() - t0, 3)
    checks += 1

async def items_snipe(item_id) -> None:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None)) as session:
        while 1:
            if len(item_ids) > 0:
                    for ids in item_ids:
                        await _id_check(session, int(ids))

async def start():
    await asyncio.gather(
        print_stats(),
        items_snipe(item_ids)
        )
asyncio.run(get_xcsrf(check_cookie))
asyncio.run(get_user_id(check_cookie))
asyncio.run(start())
