import requests
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv

load_dotenv()

def get_facebook_stats(username):
    """
        Retrieves and search Facebook statistics such as liked count, total posts, and
        followers count for a given username.
        
        :param username: The function `get_facebook_stats(username)` is designed to retrieve and display
        various statistics from a Facebook user's profile page. The function constructs a URL based on the
        provided `username`, sends a GET request to that URL, and then parses the response to extract
        information such as the number of likes, total
    """
    base_url = os.getenv("FACEBOOK_BASE_URL", "https://www.facebook.com")
    url = f"{base_url}/{username}/?__a=1"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = soup.find('meta', property='og:description')
        if metadata:
            metadata_content = metadata['content']
            liked_count = metadata_content.split(' Me gusta')[0].split(' ')[-1]
            print(f"Liked count for {username}: {liked_count}")
            posts_count = re.search(r'(\d+) publicaciones', metadata_content)
            if posts_count:
                posts_count = posts_count.group(1)
                print(f"Total posts for {username}: {posts_count}")
            else:
                print("We couldn't find the number of posts.")

            metadata_content = str(soup.find('body'))
            followers_count = re.search(r'(\d+) seguidores', metadata_content, re.IGNORECASE)
            if followers_count:
                followers_count = followers_count.group(1)
                print(f"Followers count for {username}: {followers_count}")
            else:
                print("We couldn't find the number of followers.")

if __name__ == "__main__":
    get_facebook_stats('alfanetecuador')   
