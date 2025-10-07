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
        # 在后台线程中创建同步可迭代对象，然后在主事件循环中迭代包装
        sync_iter = await asyncio.to_thread(self._client.chat.completions.create, **params)

        # 将同步迭代器包装为异步迭代器
        for chunk in sync_iter:
            yield chunk
