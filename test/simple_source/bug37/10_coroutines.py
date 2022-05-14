# Adapted from 3.7 test_coroutines.py
# fmt: off
import types
def run_async(coro):
    assert coro.__class__ in {types.GeneratorType, types.CoroutineType}
    buffer = []
    result = None
    while 1:
        try:
            buffer.append(coro.send(None))
        except StopIteration as ex:
            try:
                result = ex.args[0] if ex.args else None
                break
            finally:
                ex = None
                del ex

    return (
     buffer, result)

def test_comp_3():

    async def f(it):
        for i in it:
            yield i

    async def run_list():
        return [i + 1 async for i in f([10, 20])]

    assert run_async(run_list()) == ([], [11, 21])

    # async def run_set():
    #     return await {i + 1 async for i in f([10, 20])}

    # assert run_async(run_set()) == ([], {11, 21})

    async def run_dict():
        return {i + 1: i + 2 async for i in f([10, 20])}

    assert run_async(run_dict()), ([], {11:12,  21:22})

    async def run_gen():
        gen = (i + 1 async for i in f([10, 20]))
        return [g + 100 async for g in gen]

    assert run_async(run_gen()), ([], [111, 121])

test_comp_3()
