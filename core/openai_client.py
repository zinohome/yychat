import asyncio
from typing import Any, AsyncIterator, Dict


class AsyncOpenAIWrapper:
    """
    以线程池把同步 OpenAI 客户端的方法异步化，提供统一接口：
    - await create_chat(request_params)
    - async for chunk in create_chat_stream(request_params)
    """

    def __init__(self, sync_client: Any):
        self._client = sync_client

    async def create_chat(self, request_params: Dict[str, Any]) -> Any:
        return await asyncio.to_thread(self._client.chat.completions.create, **request_params)

    async def create_chat_stream(self, request_params: Dict[str, Any]) -> AsyncIterator[Any]:
        params = {**request_params, "stream": True}
        
        # 在后台线程中创建同步流
        def _create_stream():
            return self._client.chat.completions.create(**params)
        
        sync_stream = await asyncio.to_thread(_create_stream)
        
        # 将同步迭代器异步化
        def _next_chunk(iterator):
            try:
                return next(iterator)
            except StopIteration:
                return None
        
        iterator = iter(sync_stream)
        while True:
            chunk = await asyncio.to_thread(_next_chunk, iterator)
            if chunk is None:
                break
            yield chunk
