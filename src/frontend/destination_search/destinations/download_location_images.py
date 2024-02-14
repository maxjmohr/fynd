import requests
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import os
import sys

sys.path.append('../../../')
from backend.database import db_helpers as db


def crop_center_square(img):
    width, height = img.size
    new_size = min(width, height)
    left = (width - new_size)/2
    top = (height - new_size)/2
    right = (width + new_size)/2
    bottom = (height + new_size)/2
    return img.crop((left, top, right, bottom))

def save_image_from_url(url, save_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with Image.open(BytesIO(response.content)) as img:
            img = img.convert('RGB')
            img = crop_center_square(img)
            img = img.resize((600, 600), Image.LANCZOS)
            img.save(save_path)
    else:
        print(f'Cannot open image from URL: {url}')


if __name__ == '__main__':
    IMG_DIR = 'static/images/location_images/'

    conn, cur, engine = db.connect_to_db()
    locations_images = db.fetch_data(engine, total_object='core_locations_images')

    os.makedirs(f'{IMG_DIR}/thumbnails', exist_ok=True)
    os.makedirs(f'{IMG_DIR}/full_res', exist_ok=True)
    for location_id, img_url in tqdm(locations_images[['location_id', 'img_url']].values, desc='Downloading images'):
        try:
            save_image_from_url(img_url, f'{IMG_DIR}thumbnails/{location_id}.jpg')
        except Exception as e:
            print(f'{e} with {location_id}')
            continue
