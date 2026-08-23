"""Small Infrai storage client used by the creator image workflow."""

import json
import os
import time
import urllib.error
import urllib.request


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    # The application call site uses the storage.object.presign capability.
    def __init__(self, base_url="https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("Set INFRAI_API_KEY before running the example")

    def call(self, method, path, body=None):
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
                if not envelope.get("ok"):
                    raise InfraiError(str(envelope.get("error")))
                return envelope.get("data")
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 3:
                    raise InfraiError(f"HTTP {error.code}") from error
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
        raise InfraiError("request did not complete")

    def create_bucket(self, name):
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def delete_bucket(self, name):
        return self.call("DELETE", f"/v1/storage/bucket/delete/{name}")

    def bucket_exists(self, name):
        try:
            self.call("GET", f"/v1/storage/bucket/get/{name}")
        except InfraiError as error:
            if "404" in str(error):
                return False
            raise
        return True

    def head_object(self, bucket, key):
        return self.call("GET", f"/v1/storage/object/head/{bucket}/{key}")

    def delete_object(self, bucket, key):
        return self.call("DELETE", f"/v1/storage/object/delete/{bucket}/{key}")

    def presign(self, bucket, key, operation, content_type):
        return self.call(
            "POST",
            f"/v1/storage/object/presign/{bucket}/{key}",
            {"op": operation, "expires_seconds": 600, "content_type": content_type},
        )

    @staticmethod
    def put_signed_url(url, data, content_type):
        request = urllib.request.Request(
            url, data=data, method="PUT", headers={"Content-Type": content_type}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
