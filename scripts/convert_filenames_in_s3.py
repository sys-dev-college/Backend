import asyncio
import pathlib
import sys

import aioboto3

from app.config import settings
from app.utils.logging import logger


async def main():
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

    keys_to_rename = []
    for file in files["Contents"]:
        key_path = pathlib.Path(file["Key"])  # type: ignore
        if key_path.suffix and key_path.stem != key_path.name:
            keys_to_rename.append(key_path)

    if not keys_to_rename:
        return

    async with session.client("s3", endpoint_url=settings.DO_SPACE_URL) as s3_client:
        for key in keys_to_rename:
            logger.info("Copying %s", key)
            await s3_client.copy_object(
                Bucket=settings.DO_SPACE_BUCKET,
                CopySource=pathlib.Path(settings.DO_SPACE_BUCKET, key).as_posix(),
                Key=key.parent.joinpath(key.stem).as_posix(),
            )
            logger.info("Deleting old file %s", key)
            await s3_client.delete_object(
                Bucket=settings.DO_SPACE_BUCKET,
                Key=key.as_posix(),
            )


y_n = input("Are you sure in what you are doing? (y/n): ")
if y_n != "y":
    logger.info("Aborting")
    sys.exit(1)

asyncio.run(main())
