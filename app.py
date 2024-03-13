from flask import Flask, render_template, send_from_directory, url_for
from flask_socketio import SocketIO, emit
from pdf2image import convert_from_path
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os
import yaml
import logging

app = Flask(__name__)
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration from YAML file
def load_config(file_path):
    try:
        with open(file_path, 'r') as stream:
            config = yaml.safe_load(stream)
            return config
    except (FileNotFoundError, yaml.YAMLError) as exc:
        logger.error(f"Error loading YAML file: {exc}")
        return None

# Load PDF URLs from YAML file
config = load_config("news.yaml")
if config:
    NEWS_URLS = config.get('pdf_urls', [])
    CACHE_TIME = config.get('cache_time', 300)  # Cache for 5 minutes by default
else:
    NEWS_URLS = []
    CACHE_TIME = 300

def select_news():
    current_time = datetime.now()
    time_delta = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) % CACHE_TIME
    index = time_delta // (CACHE_TIME // len(NEWS_URLS))
    logger.info(f"Selected index: {index}")
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
            logger.error("Image not found or missing 'src' attribute.")
            return None
    except (requests.RequestException, Exception) as e:
        logger.error(f"Error retrieving cover URL: {e}")
        return None

@app.route('/')
def home():
    return render_template('home_with_image.html', image_path="current_image.jpg")

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    image_path = 'static/current_image.jpg'

    update_image()

    # emit('update_image', {'image_path': url_for('static', filename=image_path)})

def update_image():
    with app.app_context():
        news_url = select_news()
        # Generate a unique filename based on date and URL hash
        date_str = datetime.now().strftime('%Y-%m-%d')
        url_hash = hash(news_url)
        image_filename = f"{date_str}_{url_hash}.jpg"
        image_path = os.path.join('static', image_filename)
        logger.info("Updating image")

        # Check if the image for today's date and URL hash already exists
        if os.path.exists(image_path):
            logger.info(f"Using cached image: {image_path}")
            return

        logger.info(f"Grabbing url {news_url} to update image.")

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
                    logger.error(f"Error downloading image: {e}")
            else:
                logger.error(f"Failed to retrieve cover URL for {news_url}")
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
                logger.error(f"Error processing PDF: {e}")

        # Emit the event to update the image on the client side with the new path
        socketio.emit('update_image', {'image_path': url_for('static', filename=image_filename)})

def background_thread():
    while True:
        socketio.sleep(CACHE_TIME)
        update_image()

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

if __name__ == '__main__':
    socketio.start_background_task(background_thread)
    socketio.run(app, host="0.0.0.0", debug=True)
