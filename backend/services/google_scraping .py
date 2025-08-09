import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def get_google_maps_rating(api_key, business_name, location=None):
    """
        The function `get_google_maps_rating` retrieves the rating, reviews, and comments of a business on
        Google Maps using SerpAPI.
        
        :param api_key: The `api_key` parameter in the `get_google_maps_rating` function is the Serp API Key
        that you need to provide in order to make requests to the SerpAPI service for retrieving information
        about a business on Google Maps. This key is essential for authenticating your requests and
        accessing the data
        :param business_name: The `business_name` parameter in the `get_google_maps_rating` function refers
        to the name of the business for which you want to retrieve the Google Maps rating, reviews, and
        comments. This function uses the SerpAPI to fetch this information based on the provided business
        name
        :param location: The `location` parameter in the `get_google_maps_rating` function is used to
        specify the city or location to refine the search for the business on Google Maps. If provided, it
        helps narrow down the search results to the specified location, making the search more specific to
        that area. This can be
        :return: The function `get_google_maps_rating` returns a tuple containing three elements: (rating,
        reviews, comments). Each element represents different information about a business on Google Maps.
        Here is what each element represents:
    """
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
            
            return rating, reviews, comments if comments else None
        
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
                
                return result['rating'], result.get('reviews'), comments if comments else None
        
        print("No se encontró la calificación en la respuesta. Revisa el archivo serpapi_response.json")
        return None, None, None
    
    except Exception as e:
        print(f"Error al realizar la solicitud: {str(e)}")
        return None, None, None

def print_comments(comments):
    
    if not comments:
        print("No hay comentarios disponibles")
        return
    
    print("\nComentarios relevantes:")
    for i, comment in enumerate(comments, 1):
        stars = '★' * int(comment['rating']) + '☆' * (5 - int(comment['rating']))
        print(f"\n{i}. {comment['username']} - {stars}")
        print(f"   {comment['date']}")
        print(f"   {comment['text']}")

# Ejemplo de uso
if __name__ == "__main__":
    API_KEY = os.getenv("SERPAPI_API_KEY")
    if not API_KEY:
        raise ValueError("No se encontró la API Key de SerpAPI. Asegúrate de que la variable de entorno SERPAPI_API_KEY está configurada.")
        
    BUSINESS_NAME = "Alfanet Santo Domingo, Ecuador"
    LOCATION = ""  # Opcional
    
    rating, reviews, comments = get_google_maps_rating(API_KEY, BUSINESS_NAME, LOCATION)
    
    if rating is not None:
        print(f"\nEmpresa: {BUSINESS_NAME}")
        print(f"Calificación: {rating}")
        print(f"Reseñas totales: {reviews if reviews else 'No disponible'}")
        
        print_comments(comments)
    else:
        print("No se pudo obtener la información del negocio")