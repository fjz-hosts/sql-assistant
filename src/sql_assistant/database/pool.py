"""数据库连接池 — 线程安全的通用连接池实现"""

import queue
import threading
from typing import Any, Callable


class ConnectionPool:
    """通用数据库连接池

    特性：
    - 线程安全（基于 queue.Queue + threading.Lock）
    - 预创建最小连接数，减少首次查询延迟
    - 连接健康检查（每次获取前验证）
    - 自动替换失效连接
    - 支持最大连接数限制

    使用示例:
        factory = lambda: pymysql.connect(host=..., user=..., ...)
        pool = ConnectionPool(
            factory=factory,
            min_size=2,
            max_size=10,
            validation_query="SELECT 1",
        )
        conn = pool.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
        finally:
            pool.release(conn)
    """

    def __init__(
        self,
        factory: Callable[[], Any],
        min_size: int = 2,
        max_size: int = 10,
        validation_query: str | None = None,
        acquire_timeout: float = 30.0,
    ):
        if min_size < 0:
            raise ValueError("min_size 不能为负数")
        if max_size < 1:
            raise ValueError("max_size 必须 >= 1")
        if min_size > max_size:
            raise ValueError("min_size 不能大于 max_size")

        self._factory = factory
        self._min_size = min_size
        self._max_size = max_size
        self._validation_query = validation_query
        self._acquire_timeout = acquire_timeout

        self._pool: queue.Queue = queue.Queue(maxsize=max_size)
        self._total_created: int = 0
        self._lock = threading.Lock()
        self._closed = False

        self._init_pool()

    def _init_pool(self) -> None:
        for _ in range(self._min_size):
            try:
                conn = self._factory()
                self._pool.put(conn)
                with self._lock:
                    self._total_created += 1
            except Exception:
                pass

    def acquire(self) -> Any:
        """从池中获取一个连接"""
        if self._closed:
            raise RuntimeError("连接池已关闭")

        try:
            conn = self._pool.get(block=True, timeout=self._acquire_timeout)
        except queue.Empty:
            with self._lock:
                if self._total_created < self._max_size:
                    conn = self._factory()
                    self._total_created += 1
                else:
                    raise RuntimeError(
                        f"连接池已满 (max_size={self._max_size})，无法获取连接"
                    )

        if not self._validate(conn):
            conn = self._replace(conn)

        return conn

    def release(self, conn: Any) -> None:
        """将连接归还到池中"""
        if self._closed:
            self._safe_close(conn)
            return

        if not self._validate(conn):
            self._replace(conn)
            return

        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            self._safe_close(conn)
            with self._lock:
                self._total_created -= 1

    def close(self) -> None:
        """关闭连接池，释放所有连接"""
        if self._closed:
            return
        self._closed = True

        while True:
            try:
                conn = self._pool.get_nowait()
                self._safe_close(conn)
                with self._lock:
                    self._total_created -= 1
            except queue.Empty:
                break

    @property
    def size(self) -> int:
        """当前池中可用连接数"""
        return self._pool.qsize()

    @property
    def total_created(self) -> int:
        """已创建的连接总数"""
        with self._lock:
            return self._total_created

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def is_closed(self) -> bool:
        return self._closed

    def _validate(self, conn: Any) -> bool:
        if self._validation_query is None:
            return True
        try:
            cursor = conn.cursor()
            cursor.execute(self._validation_query)
            cursor.close()
            return True
        except Exception:
            return False

    def _replace(self, conn: Any) -> Any:
        self._safe_close(conn)
        with self._lock:
            self._total_created -= 1
        new_conn = self._factory()
        with self._lock:
            self._total_created += 1
        return new_conn

    @staticmethod
    def _safe_close(conn: Any) -> None:
        try:
            conn.close()
        except Exception:
            pass