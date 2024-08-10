# YouTube Data Migration and Analysis Project

## Overview

This project is designed to migrate YouTube channel data, including videos, comments, and playlists, into a MySQL database. The application is built using Streamlit for the frontend and SQLAlchemy for database interactions. It retrieves data from the YouTube API, processes it, and stores it in a structured SQL database.

## Features

- Retrieve channel details, including subscriptions, views, and description.
- Fetch all videos, playlists, and comments associated with a channel.
- Migrate the retrieved data to a MySQL database.
- Execute predefined SQL queries to analyze the migrated data.
- Display results directly in the Streamlit app.

## Prerequisites

- Python 3.7+
- MySQL database (with credentials ready)
- Google API Key with access to YouTube Data API v3

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/youtube-data-migration.git
    cd youtube-data-migration
    ```

2. **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up MySQL Database:**

   Ensure you have a MySQL database ready. Update the database connection string in the `create_engine_and_session()` function.

   ```python
   db_connection_string = "mysql+mysqlconnector://username:password@localhost/your_database"

4. **Run the Streamlit app:**

streamlit run your_script.py

5. **Enter your Google API key:**

Replace "Enter your API key" in the main() function with your actual Google API key.

# Usage

* Enter a YouTube channel ID and retrieve data.
* The app will display the retrieved data including channel details, videos, comments, and playlists.
* Migrate the retrieved data to your MySQL database.
* Execute predefined SQL queries to analyze the migrated data.

# Requirements
The project requires Python 3.7+ and the following libraries:

google-api-python-client==2.86.0
pandas==1.5.3
SQLAlchemy==2.0.15
mysql-connector-python==8.0.33
streamlit==1.22.0
python-dotenv==1.0.0
These dependencies are listed in the requirements.txt file.

# License
This project is licensed under the MIT License. See the LICENSE file for details.


