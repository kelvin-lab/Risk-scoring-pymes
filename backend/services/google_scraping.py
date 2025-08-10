import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# !NOTE: For better precision, use business names with location - example "Alfanet Santo Domingo, Ecuador"
# ! We can also use the location parameter to refine the search, 
# ! but business names with location are more reliable
def get_google_maps_rating(business_name, location=None):
    """
        The `get_google_maps_rating` function retrieves a business's rating, reviews, and comments on Google Maps using the SerpAPI.

        :param business_name: 
            The `business_name` parameter refers to the name of the business for which you want to get the Google Maps rating, reviews, and comments.

        :param location: 
            The `location` parameter is used to specify the city or location to refine the search.
        
        :return: 
            Dictionary with information about a specific company's Google maps statistics.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    params = {
        "engine": "google_maps",
        "q": business_name,
        "api_key": api_key,
        "type": "search",
        "hl": "es"
    }
    
    if location:
        params["ll"] = f"@{location}"
    
    try:
        serpapi_url = os.getenv("SERPAPI_URL", 'https://serpapi.com/search')
        response = requests.get(serpapi_url, params=params)
        data = response.json()
        
        # Extraer información de calificación y comentarios
        if 'place_results' in data:
            place_data = data['place_results']
            rating = place_data.get('rating')
            reviews = place_data.get('reviews')
            
            # Obtener comentarios relevantes si existen
            comments = []
            if 'user_reviews' in place_data and 'most_relevant' in place_data['user_reviews']:
                for review in place_data['user_reviews']['most_relevant']:
                    comment = {
                        'username': review.get('username'),
                        'rating': review.get('rating'),
                        'text': review.get('description'),
                        'date': review.get('date')
                    }
                    comments.append(comment)
            
            return {
                "source": "google",
                "business_name": business_name,
                "stats": {
                    "rating": rating,
                    "reviews": reviews
                },
                "comments": comments if comments else None
            }
        
        # Buscar en resultados orgánicos si no está en place_results
        for result in data.get('local_results', []):
            if 'rating' in result:
                comments = []
                if 'user_reviews' in result and 'most_relevant' in result['user_reviews']:
                    for review in result['user_reviews']['most_relevant']:
                        comment = {
                            'username': review.get('username'),
                            'rating': review.get('rating'),
                            'text': review.get('description'),
                            'date': review.get('date')
                        }
                        comments.append(comment)
                
                return {
                    "source": "google",
                    "business_name": business_name,
                    "stats": {
                        "rating": result['rating'],
                        "reviews": result.get('reviews')
                    },
                    "comments": comments if comments else None
                }
        
        print("No se encontró la calificación en la respuesta. Revisa el archivo serpapi_response.json")
        return {
            "source": "google",
            "business_name": business_name,
            "stats": None,
            "comments": None
        }
    
    except Exception as e:
        print(f"Error al realizar la solicitud: {str(e)}")
        return {
            "source": "google",
            "business_name": business_name,
            "stats": None,
            "comments": None
        }