import asyncio
import logging
from contextlib import asynccontextmanager
from mysql.connector.aio import connect, ProgrammingError, InterfaceError
from mysql.connector import Error

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL 连接配置（根据实际情况填写）
MYSQL_CONFIG = {
    "user": "root",
    "password": "Liukang.kangliU",
    "host": "110.42.101.233",
    "port": 3306,
    "database": "mcptest",
}

# ✅ 生产级异步连接池
class AsyncMySQLPool:
    def __init__(self, minsize=1, maxsize=5, acquire_timeout=10):
        self.minsize = minsize
        self.maxsize = maxsize
        self.acquire_timeout = acquire_timeout
        self.pool = asyncio.Queue(maxsize)
        self._initialized = False
        self._closed = False

    async def init_pool(self):
        for _ in range(self.minsize):
            conn = await connect(**MYSQL_CONFIG)
            await self.pool.put(conn)
        self._initialized = True
        logger.info(f"MySQL pool initialized with {self.minsize} connections.")

    async def acquire(self):
        if self._closed:
            raise RuntimeError("Attempted to acquire from a closed pool.")
        if not self._initialized:
            await self.init_pool()
        try:
            conn = await asyncio.wait_for(self.pool.get(), timeout=self.acquire_timeout)
            return conn
        except asyncio.TimeoutError:
            raise RuntimeError("MySQL connection pool exhausted (timeout).")

    async def release(self, conn):
        if self._closed:
            await conn.close()
        elif self.pool.qsize() < self.maxsize:
            await self.pool.put(conn)
        else:
            await conn.close()

    async def close(self):
        self._closed = True
        while not self.pool.empty():
            conn = await self.pool.get()
            await conn.close()
        logger.info("MySQL pool closed.")

    # ✅ 添加 async with 支持
    @asynccontextmanager
    async def connection(self):
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)


# ✅ 查询示例（支持上下文管理）
async def query_example(pool: AsyncMySQLPool):
    try:
        async with pool.connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("show tables;")
            rows = await cursor.fetchall()
            logger.info(f"MySQL 查询结果: {rows}")
            await cursor.close()
    except (ProgrammingError, InterfaceError, Error) as e:
        await conn.close()  # 强制销毁
        logger.exception(f"MySQL Error: {e}")

# ✅ 主程序
async def main():
    pool = AsyncMySQLPool(minsize=2, maxsize=5)
    await pool.init_pool()

    # ✅ 并发执行 10 个查询，最大连接数为 5
    tasks = [query_example(pool) for _ in range(10)]
    await asyncio.gather(*tasks, return_exceptions=True)

    tasks = [query_example(pool) for _ in range(20)]
    await asyncio.gather(*tasks, return_exceptions=True)



    # ✅ 所有任务均完成后，关闭连接池
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
