"""
Tools for AI agents with real API integrations
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class CalculatorTool:
    """A simple calculator tool."""
    
    def __init__(self):
        self.name = "calculator"
        self.description = "Perform basic mathematical operations"
    
    def execute(self, operation: str, a: float, b: float) -> float:
        """Execute a calculation."""
        operations = {
            'add': lambda x, y: x + y,
            'subtract': lambda x, y: x - y,
            'multiply': lambda x, y: x * y,
            'divide': lambda x, y: x / y if y != 0 else 0
        }
        
        if operation in operations:
            return operations[operation](a, b)
        return 0
    
    def __call__(self, operation: str, a: float, b: float) -> float:
        return self.execute(operation, a, b)


class WeatherTool:
    """Real weather API tool using WeatherAPI.com."""
    
    def __init__(self):
        self.name = "weather"
        self.description = "Get current weather and forecast for any city"
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.base_url = "https://api.weatherapi.com/v1"
    
    def execute(self, location: str, days: int = 1, unit: str = "celsius") -> Dict:
        """
        Get weather for a location.
        
        Args:
            location: City name or coordinates
            days: Number of forecast days (1-7)
            unit: 'celsius' or 'fahrenheit'
        
        Returns:
            Weather data dictionary
        """
        if not self.api_key:
            return {"error": "WEATHER_API_KEY not found in .env"}
        
        try:
            # Current weather
            current_url = f"{self.base_url}/current.json"
            current_params = {
                "key": self.api_key,
                "q": location,
                "aqi": "no"
            }
            current_response = requests.get(current_url, params=current_params, timeout=10)
            
            if current_response.status_code != 200:
                return {"error": f"City '{location}' not found"}
            
            current_data = current_response.json()
            
            # Forecast if requested
            forecast_data = None
            if days > 1:
                forecast_url = f"{self.base_url}/forecast.json"
                forecast_params = {
                    "key": self.api_key,
                    "q": location,
                    "days": days,
                    "aqi": "no"
                }
                forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
            
            result = {
                "location": f"{current_data['location']['name']}, {current_data['location']['country']}",
                "condition": current_data['current']['condition']['text'],
                "temperature": current_data['current']['temp_c'] if unit == "celsius" else current_data['current']['temp_f'],
                "unit": unit,
                "humidity": current_data['current']['humidity'],
                "wind_speed": current_data['current']['wind_kph'],
                "feels_like": current_data['current']['feelslike_c'] if unit == "celsius" else current_data['current']['feelslike_f'],
                "last_updated": current_data['current']['last_updated']
            }
            
            if forecast_data:
                forecast_days = []
                for day in forecast_data['forecast']['forecastday'][1:]:  # Skip today
                    forecast_days.append({
                        "date": day['date'],
                        "max_temp": day['day']['maxtemp_c'] if unit == "celsius" else day['day']['maxtemp_f'],
                        "min_temp": day['day']['mintemp_c'] if unit == "celsius" else day['day']['mintemp_f'],
                        "condition": day['day']['condition']['text'],
                        "chance_of_rain": day['day']['daily_chance_of_rain']
                    })
                result["forecast"] = forecast_days
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def __call__(self, location: str, days: int = 1, unit: str = "celsius") -> Dict:
        return self.execute(location, days, unit)


class FlightSearchTool:
    """Mock flight search tool (no free API available)."""
    
    def __init__(self):
        self.name = "search_flights"
        self.description = "Search for flights between cities (mock implementation)"
    
    def execute(self, origin: str, destination: str, date: str, passengers: int = 1) -> Dict:
        """
        Search for flights (mock - no free API).
        
        Args:
            origin: Departure city
            destination: Arrival city
            date: Travel date (YYYY-MM-DD)
            passengers: Number of passengers
        
        Returns:
            Mock flight results
        """
        # Mock data - in production, use a real API like Skyscanner or Amadeus
        airlines = ["United", "American", "Delta", "Air France", "British Airways"]
        prices = [350, 450, 550, 650, 750]
        durations = ["8h 30m", "9h 15m", "7h 45m", "10h 00m", "8h 00m"]
        
        import random
        results = []
        for i in range(random.randint(3, 5)):
            results.append({
                "airline": random.choice(airlines),
                "price": f"${random.choice(prices)}",
                "duration": random.choice(durations),
                "departure": f"{random.randint(6, 22):02d}:{random.randint(0, 59):02d}",
                "arrival": f"{random.randint(6, 22):02d}:{random.randint(0, 59):02d}",
                "stops": random.randint(0, 2)
            })
        
        return {
            "origin": origin,
            "destination": destination,
            "date": date,
            "passengers": passengers,
            "flights": results,
            "note": "⚠️ This is mock data. For real flight data, use a paid API like Amadeus or Skyscanner."
        }
    
    def __call__(self, origin: str, destination: str, date: str, passengers: int = 1) -> Dict:
        return self.execute(origin, destination, date, passengers)


class HotelSearchTool:
    """Mock hotel search tool."""
    
    def __init__(self):
        self.name = "search_hotels"
        self.description = "Search for hotels in a city (mock implementation)"
    
    def execute(self, city: str, check_in: str, check_out: str, guests: int = 2) -> Dict:
        """
        Search for hotels (mock).
        
        Args:
            city: City name
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
        
        Returns:
            Mock hotel results
        """
        import random
        hotels = ["Grand Hotel", "City Inn", "The Plaza", "Harbor View", "Garden Suites"]
        amenities = [
            ["WiFi", "Pool", "Gym"],
            ["WiFi", "Restaurant"],
            ["WiFi", "Pool", "Spa"],
            ["WiFi", "Gym"],
            ["WiFi", "Pool", "Restaurant", "Gym"]
        ]
        
        results = []
        for i in range(random.randint(3, 6)):
            hotel = random.choice(hotels)
            results.append({
                "name": f"{hotel} {city}",
                "price_per_night": f"${random.randint(80, 300)}",
                "rating": f"{random.randint(3, 5)}.5",
                "amenities": random.choice(amenities),
                "distance_from_center": f"{random.randint(1, 10)} km",
                "availability": random.choice(["Available", "Limited availability"])
            })
        
        return {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "hotels": results,
            "note": "⚠️ This is mock data. For real hotel data, use a paid API like Booking.com API."
        }
    
    def __call__(self, city: str, check_in: str, check_out: str, guests: int = 2) -> Dict:
        return self.execute(city, check_in, check_out, guests)


class CurrencyConverterTool:
    """Currency converter using ExchangeRate-API."""
    
    def __init__(self):
        self.name = "currency_converter"
        self.description = "Convert currency using real exchange rates"
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")
        self.base_url = "https://v6.exchangerate-api.com/v6"
        
        if not self.api_key:
            # Try alternative free API
            self.base_url = "https://api.exchangerate-api.com/v4/latest"
            self.api_key = None
    
    def execute(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """
        Convert currency.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'EUR')
        
        Returns:
            Conversion result
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        try:
            if self.api_key:
                # Paid API
                url = f"{self.base_url}/{self.api_key}/latest/{from_currency}"
                response = requests.get(url, timeout=10)
            else:
                # Free API (no key required)
                url = f"{self.base_url}/{from_currency}"
                response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {"error": "Failed to fetch exchange rates"}
            
            data = response.json()
            rates = data.get("conversion_rates", {})
            
            if to_currency not in rates:
                return {"error": f"Currency '{to_currency}' not found"}
            
            rate = rates[to_currency]
            converted = amount * rate
            
            return {
                "from": from_currency,
                "to": to_currency,
                "amount": amount,
                "rate": rate,
                "converted_amount": converted,
                "last_updated": data.get("time_last_update_utc", "N/A")
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def __call__(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        return self.execute(amount, from_currency, to_currency)


class SearchTool:
    """Web search tool using DuckDuckGo API."""
    
    def __init__(self):
        self.name = "search"
        self.description = "Search the web for information"
    
    def execute(self, query: str, max_results: int = 5) -> Dict:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum results to return
        
        Returns:
            Search results
        """
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {"error": "Search API error"}
            
            data = response.json()
            results = []
            
            # Get abstract
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", query),
                    "snippet": data.get("Abstract", ""),
                    "url": data.get("AbstractURL", ""),
                    "type": "abstract"
                })
            
            # Get related topics
            for topic in data.get("RelatedTopics", [])[:max_results - 1]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "type": "related"
                    })
            
            return {
                "query": query,
                "results": results,
                "total": len(results)
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Search error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def __call__(self, query: str, max_results: int = 5) -> Dict:
        return self.execute(query, max_results)


class CalendarTool:
    """Calendar and date utilities."""
    
    def __init__(self):
        self.name = "calendar"
        self.description = "Get date information, calculate date differences, and find weekdays"
    
    def execute(self, action: str, **kwargs) -> Dict:
        """
        Calendar operations.
        
        Actions:
            - current: Get current date/time
            - days_between: Days between two dates
            - weekday: Get weekday for a date
            - add_days: Add/subtract days from a date
        """
        if action == "current":
            now = datetime.now()
            return {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "weekday": now.strftime("%A"),
                "week_number": now.isocalendar()[1],
                "timestamp": now.isoformat()
            }
        
        elif action == "days_between":
            date1 = kwargs.get("date1")
            date2 = kwargs.get("date2", datetime.now().strftime("%Y-%m-%d"))
            
            try:
                d1 = datetime.strptime(date1, "%Y-%m-%d")
                d2 = datetime.strptime(date2, "%Y-%m-%d")
                diff = (d2 - d1).days
                return {
                    "date1": date1,
                    "date2": date2,
                    "days": abs(diff),
                    "direction": "future" if diff > 0 else "past" if diff < 0 else "same"
                }
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        elif action == "weekday":
            date = kwargs.get("date")
            try:
                d = datetime.strptime(date, "%Y-%m-%d")
                return {
                    "date": date,
                    "weekday": d.strftime("%A"),
                    "day_number": d.weekday() + 1
                }
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        elif action == "add_days":
            date = kwargs.get("date")
            days = kwargs.get("days", 0)
            
            try:
                d = datetime.strptime(date, "%Y-%m-%d")
                new_date = d + timedelta(days=days)
                return {
                    "original_date": date,
                    "days_added": days,
                    "new_date": new_date.strftime("%Y-%m-%d"),
                    "new_weekday": new_date.strftime("%A")
                }
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        return {"error": f"Unknown action: {action}"}
    
    def __call__(self, action: str, **kwargs) -> Dict:
        return self.execute(action, **kwargs)


class MapsTool:
    """Location and distance tools using OpenStreetMap Nominatim."""
    
    def __init__(self):
        self.name = "maps"
        self.description = "Get location information, coordinates, and distances"
        self.base_url = "https://nominatim.openstreetmap.org"
    
    def execute(self, action: str, **kwargs) -> Dict:
        """
        Maps operations.
        
        Actions:
            - geocode: Get coordinates for a location
            - reverse: Get location for coordinates
            - distance: Get distance between two locations
        """
        if action == "geocode":
            location = kwargs.get("location")
            if not location:
                return {"error": "Location required"}
            
            try:
                response = requests.get(
                    f"{self.base_url}/search",
                    params={
                        "q": location,
                        "format": "json",
                        "limit": 1
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "location": location,
                            "lat": float(data[0]["lat"]),
                            "lon": float(data[0]["lon"]),
                            "display_name": data[0]["display_name"],
                            "type": data[0].get("type", "unknown")
                        }
                return {"error": "Location not found"}
                
            except Exception as e:
                return {"error": f"Error: {str(e)}"}
        
        elif action == "reverse":
            lat = kwargs.get("lat")
            lon = kwargs.get("lon")
            
            if not lat or not lon:
                return {"error": "Latitude and longitude required"}
            
            try:
                response = requests.get(
                    f"{self.base_url}/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "display_name" in data:
                        return {
                            "lat": float(lat),
                            "lon": float(lon),
                            "location": data["display_name"],
                            "address": data.get("address", {})
                        }
                return {"error": "Location not found"}
                
            except Exception as e:
                return {"error": f"Error: {str(e)}"}
        
        return {"error": f"Unknown action: {action}"}
    
    def __call__(self, action: str, **kwargs) -> Dict:
        return self.execute(action, **kwargs)