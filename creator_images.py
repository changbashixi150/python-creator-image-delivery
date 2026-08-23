"""Resize a creator upload, store it, and publish a subscriber update."""

import argparse
import json
from pathlib import Path

from PIL import Image

from infrai_client import InfraiClient


BUCKET = "creator-images"
MAX_EDGE = 1600


def content_decision(width, height, max_edge=MAX_EDGE):
    scale = min(1.0, max_edge / max(width, height))
    return (round(width * scale), round(height * scale))


def process_upload(source, creator, client):
    source = Path(source)
    with Image.open(source) as image:
        target_size = content_decision(*image.size)
        image = image.convert("RGB")
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        output = source.with_name(source.stem + "-delivery.jpg")
        image.save(output, format="JPEG", quality=88, optimize=True)

    key = f"{creator}/{output.name}"
    existing = client.head_object(BUCKET, key)
    if existing.get("found"):
        status = "already-stored"
    else:
        signed = client.presign(BUCKET, key, "put", "image/jpeg")
        client.put_signed_url(signed["url"], output.read_bytes(), "image/jpeg")
        status = "stored"
    result = {"creator": creator, "key": key, "size": list(target_size), "status": status}
    print(json.dumps({"subscriber_update": result}, sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser(description="Store a resized creator image")
    parser.add_argument("image")
    parser.add_argument("--creator", default="demo-creator")
    args = parser.parse_args()
    client = InfraiClient()
    bucket_existed = client.bucket_exists(BUCKET)
    client.create_bucket(BUCKET)
    result = None
    try:
        result = process_upload(args.image, args.creator, client)
    finally:
        if result and result["status"] == "stored":
            client.delete_object(BUCKET, result["key"])
            if client.head_object(BUCKET, result["key"]).get("found"):
                raise RuntimeError("uploaded object was not deleted")
        if not bucket_existed:
            client.delete_bucket(BUCKET)
            if client.bucket_exists(BUCKET):
                raise RuntimeError("created bucket was not deleted")


if __name__ == "__main__":
    main()
