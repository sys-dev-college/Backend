import asyncio
import pathlib
import sys

import aioboto3
from sqlalchemy import text

from app.config import settings
from app.database.session import SessionManager
from app.utils.file_managers.s3 import S3FileManager
from app.utils.logging import logger


async def main():
    stmt = text("SELECT token from documents")
    async with SessionManager() as session:
        tokens = [str(key) for key in await session.scalars(stmt)]

    session = aioboto3.Session(
        aws_access_key_id=settings.DO_SPACE_KEY,
        aws_secret_access_key=settings.DO_SPACE_SECRET,
        region_name="fra1",
    )
    async with session.client(
        "s3",
        endpoint_url=settings.DO_SPACE_URL,
    ) as s3_client:
        files = await s3_client.list_objects_v2(
            Bucket=settings.DO_SPACE_BUCKET,
            Prefix=settings.DO_SPACE_FOLDER,
        )

    if not files:
        logger.error("Could not get files from bucket")
        return

    keys_to_delete = []

    for file in files["Contents"]:
        path = pathlib.Path(file["Key"])  # type: ignore
        if path.stem not in tokens:
            logger.info("Deleting %s", path.as_posix())
            keys_to_delete.append(path.as_posix())

    if keys_to_delete:
        async with S3FileManager(
            space_bucket=settings.DO_SPACE_BUCKET,
            space_folder=settings.DO_SPACE_FOLDER,
            space_url=settings.DO_SPACE_URL,
        ) as s3_connector:
            await s3_connector.delete(*keys_to_delete)


y_n = input("Are you sure in what you are doing? (y/n): ")
if y_n != "y":
    logger.info("Aborting")
    sys.exit(1)

asyncio.run(main())
