from googleapiclient.discovery import build
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.types import Text
from datetime import datetime
import streamlit as st
import re

# Define your base class
Base = declarative_base()

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(String(255), primary_key=True)
    name = Column(String(255))
    subscription_count = Column(Integer)
    view_count = Column(Integer)
    description = Column(Text)
    videos = relationship('Video', back_populates='channel')

class Video(Base):
    __tablename__ = 'videos'

    id = Column(String(255), primary_key=True)
    channel_id = Column(String(255), ForeignKey('channels.id'))
    title = Column(String(255))
    description = Column(Text)
    published_at = Column(DateTime)
    view_count = Column(Integer)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    favorite_count = Column(Integer)
    comment_count = Column(Integer)
    duration = Column(String(50))
    thumbnail = Column(String(255))
    caption_status = Column(String(50))
    channel = relationship('Channel', back_populates='videos')
    comments = relationship('Comment', back_populates='video')

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(String(255), primary_key=True)
    video_id = Column(String(255), ForeignKey('videos.id'))
    text = Column(Text)
    author = Column(String(255))
    published_at = Column(DateTime)
    video = relationship('Video', back_populates='comments')

def create_engine_and_session():
    db_connection_string = "mysql+mysqlconnector://root:12345678@localhost/youtube_data"
    engine = create_engine(db_connection_string)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, session

def get_channel_details(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    )
    response = request.execute()
    
    channel = response['items'][0]
    return {
        'id': channel['id'],
        'name': channel['snippet']['title'],
        'subscription_count': int(channel['statistics']['subscriberCount']),
        'view_count': int(channel['statistics']['viewCount']),
        'description': channel['snippet']['description']
    }

# New function to retrieve playlist details
def get_channel_playlists(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    playlists = []
    
    next_page_token = None
    while True:
        request = youtube.playlists().list(
            part='id,snippet',
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            playlists.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'published_at': item['snippet']['publishedAt']
            })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return playlists



def get_all_channel_videos(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    
    next_page_token = None
    while True:
        request = youtube.search().list(
            part='id,snippet',
            channelId=channel_id,
            maxResults=50,
            type='video',
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            videos.append({
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'published_at': item['snippet']['publishedAt']
            })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos

def get_video_details(api_key, video_ids):
    youtube = build('youtube', 'v3', developerKey=api_key)
    video_details = []
    
    for i in range(0, len(video_ids), 50):  # Process in batches of 50
        request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids[i:i + 50])
        )
        response = request.execute()
        
        for item in response['items']:
            video_details.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'published_at': item['snippet']['publishedAt'],
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
                'dislike_count': int(item['statistics'].get('dislikeCount', 0)),
                'favorite_count': int(item['statistics'].get('favoriteCount', 0)),
                'comment_count': int(item['statistics'].get('commentCount', 0)),
                'duration': item['contentDetails'].get('duration', ''),
                'thumbnail': item['snippet']['thumbnails']['default']['url'],
                'caption_status': item['contentDetails'].get('caption', '')
            })
    
    return video_details

def get_video_comments(api_key, video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []
    
    try:
        next_page_token = None
        while True:
            request = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'id': item['id'],
                    'video_id': video_id,
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'published_at': comment['publishedAt']
                })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
    except:
        # If comments are disabled or there's an error, just return an empty list
        pass
    
    return comments

def create_dataframes(channel_details, video_details, all_comments, playlist_details):
    channel_df = pd.DataFrame([{
        'Channel_Id': channel_details['id'],
        'Channel_Name': channel_details['name'],
        'Subscription_Count': channel_details['subscription_count'],
        'Channel_Views': channel_details['view_count'],
        'Channel_Description': channel_details['description']
    }])

    videos_data = []
    for video in video_details:
        video_data = {
            'Video_Id': video['id'],
            'Channel_Id': channel_details['id'],
            'Video_Name': video['title'],
            'Video_Description': video['description'],
            'PublishedAt': video['published_at'],  # Store as string
            'View_Count': video['view_count'],
            'Like_Count': video['like_count'],
            'Dislike_Count': video['dislike_count'],
            'Favorite_Count': video['favorite_count'],
            'Comment_Count': video['comment_count'],
            'Duration': video['duration'],
            'Thumbnail': video['thumbnail'],
            'Caption_Status': video['caption_status']
        }
        videos_data.append(video_data)

    videos_df = pd.DataFrame(videos_data)
    comments_df = pd.DataFrame(all_comments)

    playlists_data = []
    for playlist in playlist_details:
        playlist_data = {
            'Playlist_Id': playlist['id'],
            'Channel_Id': channel_details['id'],
            'Playlist_Name': playlist['title'],
            'Playlist_Description': playlist['description'],
            'PublishedAt': playlist['published_at']  # Store as string
        }
        playlists_data.append(playlist_data)

    playlists_df = pd.DataFrame(playlists_data)
    
    return channel_df, videos_df, comments_df, playlists_df  # Return four dataframes

def migrate_to_sql(channel_df, videos_df, comments_df):
    try:
        engine, session = create_engine_and_session()

        # Insert data into the channels table
        for index, row in channel_df.iterrows():
            existing_channel = session.query(Channel).filter(Channel.id == row['Channel_Id']).first()
            if not existing_channel:
                session.execute(Channel.__table__.insert().values(
                    id=row['Channel_Id'],
                    name=row['Channel_Name'],
                    subscription_count=row['Subscription_Count'],
                    view_count=row['Channel_Views'],
                    description=row['Channel_Description']
                ))

        # Insert data into the videos table
        for index, row in videos_df.iterrows():
            existing_video = session.query(Video).filter(Video.id == row['Video_Id']).first()
            if not existing_video:
                session.execute(Video.__table__.insert().values(
                    id=row['Video_Id'],
                    channel_id=row['Channel_Id'],
                    title=row['Video_Name'],
                    description=row['Video_Description'],
                    published_at=convert_datetime(row['PublishedAt']),  # Convert datetime
                    view_count=row['View_Count'],
                    like_count=row['Like_Count'],
                    dislike_count=row['Dislike_Count'],
                    favorite_count=row['Favorite_Count'],
                    comment_count=row['Comment_Count'],
                    duration=row['Duration'],
                    thumbnail=row['Thumbnail'],
                    caption_status=row['Caption_Status']
                ))

        # Insert data into the comments table
        for index, row in comments_df.iterrows():
            existing_comment = session.query(Comment).filter(Comment.id == row['id']).first()
            if not existing_comment:
                session.execute(Comment.__table__.insert().values(
                    id=row['id'],
                    video_id=row['video_id'],
                    text=row['text'],
                    author=row['author'],
                    published_at=convert_datetime(row['published_at'])  # Convert datetime
                ))

        # Commit the changes
        session.commit()
        
        return True  # Indicate success
    except Exception as e:
        session.rollback()
        st.error(f"An error occurred during database migration: {e}")
        return False  # Indicate failure

def convert_duration_to_seconds(duration):
    """Convert ISO 8601 duration to seconds."""
    regex = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = regex.match(duration)
    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds

def seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def convert_datetime(dt_string):
    return datetime.strptime(dt_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
    
def execute_query(engine, query):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

def main():
    st.title("YouTube Data Migration")

    api_key = "Enter Your API Key"  # Hardcoded API key

    # Initialize session state variables if they don't exist
    if 'stored_channels' not in st.session_state:
        st.session_state.stored_channels = []  # List of stored channels
    if 'selected_channel' not in st.session_state:
        st.session_state.selected_channel = None
    if 'data_retrieved' not in st.session_state:
        st.session_state.data_retrieved = False  # Track if data has been retrieved
    if 'data_migrated' not in st.session_state:
        st.session_state.data_migrated = False  # Track if data has been migrated

    # Button to get channel details and store data
    channel_id = st.text_input("Enter Channel ID")

    if st.button("Get Results and Store Data"):
        if channel_id:
            try:
                # Retrieve channel details
                channel_details = get_channel_details(api_key, channel_id)

                # Get all videos for the channel
                videos = get_all_channel_videos(api_key, channel_id)
                video_ids = [video['id'] for video in videos]

                # Get video details for the retrieved video IDs
                video_details = get_video_details(api_key, video_ids)

                # Get comments for all videos
                all_comments = []
                for video_id in video_ids:
                    comments = get_video_comments(api_key, video_id)
                    all_comments.extend(comments)

                # Get playlists for the channel
                playlists = get_channel_playlists(api_key, channel_id)

                # Create dataframes from the retrieved channel, video, comment, and playlist details
                channel_df, videos_df, comments_df, playlists_df = create_dataframes(channel_details, video_details, all_comments, playlists)

                # Store the retrieved channel data including playlists
                stored_data = {
                    'channel_id': channel_details['id'],
                    'channel': channel_df,
                    'videos': videos_df,
                    'comments': comments_df,
                    'playlists': playlists_df  # Include playlists
                }
                st.session_state.stored_channels.append(stored_data)

                # Set the flag to indicate data has been retrieved
                st.session_state.data_retrieved = True  
                
                # Display the dataframes
                st.subheader("Channel Data")
                st.write(channel_df)

                st.subheader("Playlists Data")
                st.write(playlists_df)

                st.subheader("Videos Data")
                st.write(videos_df)

                st.subheader("Comments Data")
                st.write(comments_df)



                st.success("Data Retrieved and Stored Successfully")

            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Display the channel selection dropdown only after successful data retrieval
    if st.session_state.data_retrieved:
        st.subheader("Select a channel to migrate data to SQL")
        st.session_state.selected_channel = st.selectbox(
            "Select a channel",
            options=[channel['channel_id'] for channel in st.session_state.stored_channels],
            index=0 if st.session_state.stored_channels else None,
        )

        if st.button("Migrate Data to SQL"):
            if st.session_state.selected_channel:
                selected_channel_data = next(
                    (channel for channel in st.session_state.stored_channels if channel['channel_id'] == st.session_state.selected_channel), None
                )
                if selected_channel_data:
                    success = migrate_to_sql(selected_channel_data['channel'], selected_channel_data['videos'], selected_channel_data['comments'])
                    if success:
                        st.success("Data migrated to SQL successfully!")
                        st.session_state.data_migrated = True  # Set the flag to indicate data has been migrated
                        # Remove the migrated channel from stored channels
                        st.session_state.stored_channels.remove(selected_channel_data)
                    else:
                        st.error("Data migration to SQL failed.")

        # Queries and their corresponding descriptions
        queries = {
            "What are the names of all the videos and their corresponding channels?": """
                SELECT videos.title AS Video_Name, channels.name AS Channel_Name 
                FROM videos 
                JOIN channels ON videos.channel_id = channels.id;
            """,
            "Which channels have the most number of videos, and how many videos do they have?": """
                SELECT channels.name AS Channel_Name, COUNT(videos.id) AS Video_Count 
                FROM channels 
                JOIN videos ON channels.id = videos.channel_id 
                GROUP BY channels.name 
                ORDER BY Video_Count DESC;
            """,
            "What are the top 10 most viewed videos and their respective channels?": """
                SELECT videos.title AS Video_Name, channels.name AS Channel_Name, videos.view_count AS View_Count 
                FROM videos 
                JOIN channels ON videos.channel_id = channels.id 
                ORDER BY videos.view_count DESC 
                LIMIT 10;
            """,
            "How many comments were made on each video, and what are their corresponding video names?": """
                SELECT videos.title AS Video_Name, COUNT(comments.id) AS Comment_Count 
                FROM videos 
                JOIN comments ON videos.id = comments.video_id 
                GROUP BY videos.title;
            """,
            "Which videos have the highest number of likes, and what are their corresponding channel names?": """
                SELECT videos.title AS Video_Name, channels.name AS Channel_Name, videos.like_count AS Like_Count 
                FROM videos 
                JOIN channels ON videos.channel_id = channels.id 
                ORDER BY videos.like_count DESC;
            """,
            "What is the total number of likes and dislikes for each video, and what are their corresponding video names?": """
                SELECT videos.title AS Video_Name, videos.like_count AS Like_Count, videos.dislike_count AS Dislike_Count 
                FROM videos;
            """,
            "What is the total number of views for each channel, and what are their corresponding channel names?": """
                SELECT channels.name AS Channel_Name, channels.view_count AS View_Count 
                FROM channels;
            """,
            "What are the names of all the channels that have published videos in the year 2022?": """
                SELECT DISTINCT channels.name AS Channel_Name 
                FROM channels 
                JOIN videos ON channels.id = videos.channel_id 
                WHERE YEAR(videos.published_at) = 2022;
            """,
            "What is the average duration of all videos in each channel, and what are their corresponding channel names?": """
                SELECT 
                    channels.name AS Channel_Name, 
                    AVG(
                        COALESCE(NULLIF(SUBSTRING_INDEX(SUBSTRING_INDEX(videos.duration, 'H', 1), 'PT', -1), '') * 3600, 0) +
                        COALESCE(NULLIF(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(videos.duration, 'M', 1), 'H', -1), 'PT', -1), '') * 60, 0) +
                        COALESCE(NULLIF(SUBSTRING_INDEX(SUBSTRING_INDEX(videos.duration, 'S', 1), 'M', -1), ''), 0)
                    ) AS Average_Duration_Seconds
                FROM channels 
                JOIN videos ON channels.id = videos.channel_id 
                GROUP BY channels.name
            """,
            "Which videos have the highest number of comments, and what are their corresponding channel names?": """
                SELECT 
                    videos.title AS Video_Name, 
                    channels.name AS Channel_Name, 
                    COUNT(comments.id) AS Comment_Count 
                FROM 
                    videos 
                JOIN 
                    channels ON videos.channel_id = channels.id 
                JOIN 
                    comments ON videos.id = comments.video_id 
                GROUP BY 
                    videos.title, channels.name 
                ORDER BY 
                    Comment_Count DESC;
            """
        }

        # Display the query selection dropdown only after successful migration
        if st.session_state.data_migrated:
            st.subheader("Select a query to execute")
            selected_query = st.selectbox(
                "Select a query",
                options=list(queries.keys()),
                index=0
            )
        
            # Execute the query when the selection changes
            query = queries[selected_query]
            engine, session = create_engine_and_session()
            result_df = execute_query(engine, query)
            
            # Convert the average duration to HH:MM:SS format if the selected query is the 9th one
            if selected_query == "What is the average duration of all videos in each channel, and what are their corresponding channel names?":
                result_df['Average_Duration'] = result_df['Average_Duration_Seconds'].apply(seconds_to_hms)
                result_df.drop('Average_Duration_Seconds', axis=1, inplace=True)
            
            st.write(result_df)


if __name__ == "__main__":
    main()
