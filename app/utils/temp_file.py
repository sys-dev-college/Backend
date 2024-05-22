from typing import AsyncGenerator, Tuple

from aiofiles.tempfile import NamedTemporaryFile, TemporaryDirectory
from aiofiles.threadpool.binary import AsyncBufferedReader

from app.config import settings


async def temp_dir_and_file() -> AsyncGenerator[
    Tuple[AsyncBufferedReader, str],
    None,
]:
    async with (
        TemporaryDirectory(dir=settings.TMP_STORAGE_PATH) as tmp_dir,
        NamedTemporaryFile("w+b", dir=tmp_dir) as f,
    ):
        yield f, tmp_dir
