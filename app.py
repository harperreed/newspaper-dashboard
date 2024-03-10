from flask import Flask, render_template, send_from_directory
from pdf2image import convert_from_path
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os
import yaml

app = Flask(__name__)

# Load PDF URLs from YAML file
try:
    with open("news.yaml", 'r') as stream:
        config = yaml.safe_load(stream)
        NEWS_URLS = config.get('pdf_urls', [])
        CACHE_TIME = config.get('cache_time', 300)  # Cache for 5 minutes by default
except (FileNotFoundError, yaml.YAMLError) as exc:
    print(f"Error loading YAML file: {exc}")
    NEWS_URLS = []
    CACHE_TIME = 300

def select_news():
    current_time = datetime.now()
    time_delta = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) % CACHE_TIME
    index = time_delta // (CACHE_TIME // len(NEWS_URLS))
    print(f"Selected index: {index}")
    return NEWS_URLS[index]

def get_cover_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tag = soup.find('img', attrs={'id': 'giornale-img'})
        if img_tag and 'src' in img_tag.attrs:
            return 'https://www.frontpages.com' + img_tag['src']
        else:
            raise Exception("Image not found or missing 'src' attribute.")
    except (requests.RequestException, Exception) as e:
        print(f"Error retrieving cover URL: {e}")
        return None

@app.route('/')
def home():
    return render_template('home_with_image.html', image_path="current_image.jpg", cache_time=CACHE_TIME)

@app.route('/static/current_image.jpg')
def current_image():
    news_url = select_news()
    image_path = 'static/current_image.jpg'

    # Check if the cached image is recent enough
    if os.path.exists(image_path):
        modification_time = datetime.fromtimestamp(os.path.getmtime(image_path))
        if (datetime.now() - modification_time).seconds < CACHE_TIME:
            time_left = CACHE_TIME - (datetime.now() - modification_time).seconds
            print(f"Using cached image. Cache time left: {time_left} seconds")
            print(f"Selected URL: {news_url}")
            print(f"Selected index: {NEWS_URLS.index(news_url)}")
            print(f"Cache for {CACHE_TIME} seconds")
            return send_from_directory('static', 'current_image.jpg')

    # Check if the URL is a frontpages.com URL or a PDF URL
    if "frontpages.com" in news_url:
        cover_url = get_cover_url(news_url)
        if cover_url:
            try:
                image_response = requests.get(cover_url)
                image_response.raise_for_status()
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
            except requests.RequestException as e:
                print(f"Error downloading image: {e}")
    else:
        try:
            response = requests.get(news_url)
            response.raise_for_status()
            temp_pdf = "temp_file.pdf"
            with open(temp_pdf, 'wb') as f:
                f.write(response.content)
            images = convert_from_path(temp_pdf, first_page=1, last_page=1)
            first_page_image = images[0]
            first_page_image.save(image_path, 'JPEG')
            os.remove(temp_pdf)
        except (requests.RequestException, Exception) as e:
            print(f"Error processing PDF: {e}")

    return send_from_directory('static', 'current_image.jpg')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
