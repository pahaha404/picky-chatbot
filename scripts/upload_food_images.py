import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = PROJECT_ROOT / "static" / "foods" / "generated"
BUCKET_NAME = os.getenv("SUPABASE_FOOD_BUCKET", "food-images")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env.local")
    load_dotenv(PROJECT_ROOT / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set.")

    client = create_client(supabase_url, supabase_key)

    try:
        bucket_names = {bucket.name for bucket in client.storage.list_buckets()}
    except Exception as exc:
        raise RuntimeError(f"Could not list Supabase storage buckets: {exc}") from exc

    if BUCKET_NAME not in bucket_names:
        raise RuntimeError(
            f"Supabase bucket '{BUCKET_NAME}' does not exist. "
            "Create it as a public bucket in Supabase Storage first."
        )

    image_paths = sorted(IMAGE_DIR.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"No JPG files found in {IMAGE_DIR}")

    bucket = client.storage.from_(BUCKET_NAME)
    public_base_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}"

    for image_path in image_paths:
        storage_path = image_path.name
        content_type = mimetypes.guess_type(image_path.name)[0] or "image/png"

        with image_path.open("rb") as file:
            bucket.upload(
                storage_path,
                file,
                file_options={
                    "content-type": content_type,
                    "upsert": "true",
                },
            )

        print(f"{image_path.name} -> {public_base_url}/{storage_path}")

    print()
    print("Set this on Railway if you want Kakao cards to use Supabase Storage URLs:")
    print(f"FOOD_IMAGE_BASE_URL={public_base_url}")


if __name__ == "__main__":
    main()
