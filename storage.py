from __future__ import annotations
from io import BytesIO
from pathlib import Path
from PIL import Image
import boto3
from botocore.config import Config as BotoConfig
from flask import current_app
from werkzeug.datastructures import FileStorage
from security import safe_storage_name, allowed_file


class UploadError(Exception):
    pass


def validate_image(file: FileStorage) -> tuple[bytes, str]:
    if not file or not file.filename:
        raise UploadError('No image selected.')
    if not allowed_file(file.filename):
        raise UploadError('Only JPG, PNG, and WEBP images are allowed.')
    data = file.read()
    if not data:
        raise UploadError('Empty image file.')
    max_bytes = current_app.config['MAX_CONTENT_LENGTH']
    if len(data) > max_bytes:
        raise UploadError(f'Image too large. Limit is {current_app.config["MAX_CONTENT_LENGTH_MB"]} MB.')
    try:
        image = Image.open(BytesIO(data))
        image.verify()
    except Exception as exc:
        raise UploadError('Uploaded file is not a valid image.') from exc
    return data, (file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg')


def normalize_image(data: bytes, ext: str) -> tuple[bytes, str, str]:
    image = Image.open(BytesIO(data)).convert('RGB')
    image.thumbnail((1800, 1400))
    out = BytesIO()
    image.save(out, format='WEBP', quality=86, method=6)
    return out.getvalue(), 'webp', 'image/webp'


def _r2_client():
    return boto3.client(
        's3',
        endpoint_url=current_app.config['CLOUDFLARE_R2_ENDPOINT_URL'],
        aws_access_key_id=current_app.config['CLOUDFLARE_R2_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['CLOUDFLARE_R2_SECRET_ACCESS_KEY'],
        config=BotoConfig(signature_version='s3v4'),
        region_name='auto',
    )


def save_room_image(file: FileStorage) -> dict:
    raw, ext = validate_image(file)
    data, final_ext, content_type = normalize_image(raw, ext)
    key = safe_storage_name(file.filename).rsplit('.', 1)[0] + f'.{final_ext}'

    provider = current_app.config['STORAGE_PROVIDER'].lower()
    if provider == 'r2':
        bucket = current_app.config['CLOUDFLARE_R2_BUCKET']
        if not bucket:
            raise UploadError('R2 bucket is not configured.')
        client = _r2_client()
        client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        public = current_app.config.get('CLOUDFLARE_R2_PUBLIC_URL')
        if public:
            url = f'{public.rstrip("/")}/{key}'
        else:
            url = client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
        return {'url': url, 'storage_key': key, 'provider': 'r2'}

    folder = Path(current_app.root_path) / current_app.config['LOCAL_UPLOAD_FOLDER']
    dest = folder / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {'url': f'/uploads/{key}', 'storage_key': key, 'provider': 'local'}


def delete_object(storage_key: str):
    if not storage_key:
        return
    provider = current_app.config['STORAGE_PROVIDER'].lower()
    if provider == 'r2':
        _r2_client().delete_object(Bucket=current_app.config['CLOUDFLARE_R2_BUCKET'], Key=storage_key)
    else:
        path = Path(current_app.root_path) / current_app.config['LOCAL_UPLOAD_FOLDER'] / storage_key
        if path.exists():
            path.unlink()
