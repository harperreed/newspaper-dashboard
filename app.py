from flask import Flask, render_template, send_file
from flask import Flask, render_template, send_file, send_from_directory
from pdf2image import convert_from_path
from bs4 import BeautifulSoup

import requests
from datetime import datetime
import os
import yaml

app = Flask(__name__)

# Load PDF URLs from YAML file
with open("news.yaml", 'r') as stream:
    try:
        NEWS_URLS = yaml.safe_load(stream)['pdf_urls']
    except yaml.YAMLError as exc:
        print(exc)
        NEWS_URLS = []

CACHE_TIME = 300  # Cache for 5 minutes

def select_news():
    current_time = datetime.now()
    time_delta = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) % CACHE_TIME
    index = time_delta // (CACHE_TIME // len(NEWS_URLS))
    print(f"Selected index: {index}")
    return NEWS_URLS[index]

def get_cover_url(url):
    try:
        # Fetch the content of the URL
        response = requests.get(url)
        # Raise an exception if the response was an error
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the image and construct the full URL
        img_tag = soup.find('img', attrs={'id': 'giornale-img'})
        if img_tag and 'src' in img_tag.attrs:
            return 'https://www.frontpages.com' + img_tag['src']
        else:
            return "Image not found or missing 'src' attribute."
    except requests.RequestException as e:
        return f"Request failed: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/')
def home():
    return render_template('home_with_image.html', image_path="current_image.jpg")

@app.route('/static/current_image.jpg')
def current_image():
    # Define a cache timeout (in seconds)
    news_url = select_news()
    cache_timeout = CACHE_TIME

    # Check if the cached image is recent enough
    image_path = 'static/current_image.jpg'
    if os.path.exists(image_path):
        modification_time = datetime.fromtimestamp(os.path.getmtime(image_path))
        if (datetime.now() - modification_time).seconds < cache_timeout:
            time_left = cache_timeout - (datetime.now() - modification_time).seconds
            print(f"Using cached image. Cache time left: {time_left} seconds")
            print(f"Selected URL: {news_url}")
            print(f"Selected index: {NEWS_URLS.index(news_url)}")
            print(f"Cache for {cache_timeout} seconds")
            return send_from_directory('static', 'current_image.jpg')
            return send_from_directory('static', 'current_image.jpg')


    # Check if the URL is a frontpages.com URL or a PDF URL
    if "frontpages.com" in news_url:
        # Download the image from frontpages.com
        image_response = requests.get(get_cover_url(news_url))
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
    else:
        # Assume the URL is a direct link to a PDF
        response = requests.get(news_url)

        # Save the PDF temporarily
        temp_pdf = "temp_file.pdf"
        with open(temp_pdf, 'wb') as f:
            f.write(response.content)

        # Convert the first page of the PDF to an image
        images = convert_from_path(temp_pdf, first_page=1, last_page=1)
        first_page_image = images[0]
        first_page_image.save(image_path, 'JPEG')

        # Remove the temporary PDF file
        os.remove(temp_pdf)

    # Render template with the path to the image
    return send_from_directory('static', 'current_image.jpg')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
