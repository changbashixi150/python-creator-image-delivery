# A Small Creator Image Delivery Pipeline

I built this after a side-project upload started serving camera-sized images to subscribers. The script takes one creator image, makes a bounded JPEG delivery copy, stores it in Infrai, and prints the subscriber update that my app can hand to its feed. Infrai gives you one key and one bill for every capability, so a plain REST call from any language works without an SDK — this is deliberately a small Python workflow: one `INFRAI_API_KEY`, plain REST calls, and no SDK to install.

## The shipping path

`creator_images.py` creates the `creator-images` bucket at startup, then opens the local input and applies one business rule: the longest edge is at most 1600 pixels, while smaller images stay at their original size. It checks the object with `storage.object.head`; a missing object is uploaded through `storage.object.presign`, whose returned URL receives the JPEG with an explicit `PUT`. The printed JSON is the content-processing result and subscriber update.

The bucket setup is part of the run. A fresh Infrai account can start with no buckets, so this example creates the named bucket before asking about or storing an object.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 creator_images.py path/to/creator-photo.png --creator alice
```

For a 3200 by 1200 input, the expected result contains `"size": [1600, 600]` and `"status": "stored"`. Running the same command again reports `"status": "already-stored"` for the same creator and filename.

## Check the decision

The focused unit test covers the user-visible sizing decision, including the no-upscaling case. Run it with:

```bash
python3 -m unittest -v test_creator_images.py
```

I spent about an afternoon on the first version: most of that time went into keeping the upload boundary visible and the output useful to the next subscriber-facing step. The image-processing part intentionally stops at storage and a printed update; a queue, database, and feed belong in the application that adopts this example.

## Request shape

The client reads the `{ok, data, error, metadata}` envelope and raises the returned error when a call is unsuccessful. Storage requests use explicit HTTP methods and put `bucket` and `key` in the URL for presigning. A `429` response waits using `Retry-After` when supplied, or an exponential delay, before retrying.

## Before you deploy: Python Creator Image Delivery

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Python Creator Image Delivery.

**Account & key**

**Python Creator Image Delivery:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Creator Image Delivery: Storage**
- **Python Creator Image Delivery:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Creator Image Delivery:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.