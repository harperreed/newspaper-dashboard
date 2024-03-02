from flask import Flask, render_template, send_file
from pdf2image import convert_from_path
import requests
from datetime import datetime
import os
import yaml

app = Flask(__name__)

# Load PDF URLs from YAML file
with open("pdfs.yaml", 'r') as stream:
    try:
        PDF_URLS = yaml.safe_load(stream)['pdf_urls']
    except yaml.YAMLError as exc:
        print(exc)
        PDF_URLS = []

def select_pdf():
    index = (datetime.now().minute // 10) % len(PDF_URLS)
    return PDF_URLS[index]

@app.route('/')
def home():
    pdf_url = select_pdf()
    response = requests.get(pdf_url)

    # Save the PDF temporarily
    temp_pdf = "temp_file.pdf"
    with open(temp_pdf, 'wb') as f:
        f.write(response.content)

    # Convert the first page of the PDF to an image
    images = convert_from_path(temp_pdf, first_page=1, last_page=1)
    first_page_image = images[0]
    image_path = 'static/current_image.jpg'
    first_page_image.save(image_path, 'JPEG')

    # Remove the temporary PDF file
    os.remove(temp_pdf)

    # Render template with the path to the image
    return render_template('home_with_image.html', image_path=image_path)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
