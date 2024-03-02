# Newspaper Dashboard

This Flask application dynamically selects a PDF from a predefined list and displays it as an image on a webpage. The application cycles through the PDFs every ten minutes. It demonstrates basic Flask routing, template rendering, and working with external resources and Docker.

This is perfect for displaying a digital newspaper on a large screen in a public space, such as a library or community center.

## Features

- Dynamically selects a PDF from a list stored in a YAML file.
- Converts the selected PDF to an image.
- Displays the image on a webpage, filling the entire screen.
- Dockerized Flask application for easy setup and deployment.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Docker and Docker Compose installed on your machine (for Docker deployment).
- Python 3.8 or newer (if running locally without Docker).

## Local Setup

To set up the project locally, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/harperreed/newspaper-dashboard
    cd newspaper-dashboard
    ```

2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the Flask application:

    ```bash
    flask run
    ```

Your app should now be running on [http://localhost:5000](http://localhost:5000).

## Docker Deployment

To deploy the application using Docker, follow these steps:

1. Build the Docker image:

    ```bash
    docker-compose up --build
    ```

This command builds the Docker image for your application and starts it. The app will be accessible on [http://localhost:5000](http://localhost:5000).

## Configuration

- PDF URLs are stored in `pdfs.yml`. Update this file to change the list of PDFs the application cycles through.
- The Docker environment can be adjusted by editing the `Dockerfile` and `docker-compose.yml`.

## Contributing

We welcome contributions to this project. If you have suggestions for improving this application, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
