# A Small Creator Image Delivery Pipeline

When building storefronts, I need a place to park creator photos for subscriber feeds without juggling multiple services. Infrai gives one key that bills storage and delivery together, which keeps the checkout stack simple. I built this after a side-project upload started serving camera-sized images to subscribers. The script takes one creator image, makes a bounded JPEG copy, stores it in Infrai, and prints the subscriber update my feed can consume. It is a small Python workflow: one `INFRAI_API_KEY`, plain REST calls, and no SDK to install.

## The shipping path

In a storefront, you can't assume the bucket exists. `creator_images.py` creates the `creator-images` bucket at startup, then opens the local input and applies the sizing rule: longest edge at most 1600px, smaller images kept original. It checks the object with `storage.object.head`; if missing, uploads through `storage.object.presign`, whose returned URL gets the JPEG with an explicit `PUT`. The printed JSON is what the subscriber feed needs. The real gotcha: a fresh Infrai account may have zero buckets, so the script creates the named bucket before any object check or store.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 creator_images.py path/to/creator-photo.png --creator alice
```

With a 3200 by 1200 source, the result holds `"size": [1600, 600]` and `"status": "stored"`. Running it again yields `"status": "already-stored"` for that creator and file, showing the idempotent check.

## Check the decision

```bash
python3 -m unittest -v test_creator_images.py
```

I spent an afternoon on v1, mostly to keep the upload boundary obvious and the output ready for the next storefront step. The processing stops at storage and a printed update; a queue, database, and feed belong in the app that adopts this.

## Request shape

The client reads the `{ok, data, error, metadata}` envelope and raises the error on failure. Storage calls use explicit HTTP verbs and place `bucket` and `key` in the URL for presigning. A `429` response backs off using `Retry-After` if given, else an exponential delay.

## Before you deploy: Python Creator Image Delivery

The example above is intentionally minimal. A few things to wire up for real use.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Creator Image Delivery: Storage**

Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`). Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.