import asyncio

data = [0]

async def foo1(sleep_time):
    while True:
        print(data)
        await asyncio.sleep(sleep_time)

async def foo2(sleep_time):
    while True:
        data.append(1)
        await asyncio.sleep(sleep_time)

loop = asyncio.get_event_loop()
loop.create_task(foo1(1))
loop.create_task(foo2(5))
loop.run_forever()