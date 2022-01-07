import asyncio

from liminus.settings import logger


_background_tasks = []


def run_background_task(coro):
    task = asyncio.create_task(coro)

    global _background_tasks
    _background_tasks.append(task)

    if len(_background_tasks) > 100:
        trim_tasklist()


def trim_tasklist():
    global _background_tasks

    # clean up old tasks
    _background_tasks = [t for t in _background_tasks if not t.done()]


async def complete_all_background_tasks(timeout: int):
    try:
        trim_tasklist()
        all_tasks = asyncio.gather(*_background_tasks)
        await asyncio.wait_for(all_tasks, timeout=timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logger.warn(f'complete_all_background_tasks timed out after {timeout} seconds: {_background_tasks}')
