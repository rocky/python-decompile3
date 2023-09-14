# Bug from Python 3.4 asyncio/tasks.py
# def as_completed(fs, *, loop=None):
#     todo = {async(f, loop=loop) for f in set(fs)}


async def run_list2():
    return {i for pair in ([10, 20], [30, 40]) async for i in pair}
