# backend/services/live_data.py
import aiohttp
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class LiveDataService:
    """
    Service for fetching live data from external APIs
    - Weather
    - Stock prices
    - News
    - Web search
    """
    
    def __init__(
        self,
        weather_api_key: Optional[str] = None,
        news_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None
    ):
        self.weather_api_key = weather_api_key
        self.news_api_key = news_api_key
        self.alpha_vantage_key = alpha_vantage_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Live data service initialized")
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # ==================== WEATHER ====================
    
    async def get_weather(
        self,
        city: str,
        country_code: str = "US"
    ) -> Dict[str, Any]:
        """
        Get current weather for a city
        
        Args:
            city: City name
            country_code: ISO country code
            
        Returns:
            Weather data
        """
        try:
            await self._ensure_session()
            
            # Using OpenWeatherMap API (free tier)
            if not self.weather_api_key:
                # Fallback to mock data if no API key
                logger.warning("No weather API key, returning mock data")
                return {
                    "city": city,
                    "temperature": 72,
                    "conditions": "Partly Cloudy",
                    "humidity": 65,
                    "wind_speed": 8,
                    "description": f"Mock weather data for {city}"
                }
            
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": f"{city},{country_code}",
                "appid": self.weather_api_key,
                "units": "imperial"  # Fahrenheit
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "city": data["name"],
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "conditions": data["weather"][0]["main"],
                        "description": data["weather"][0]["description"],
                        "humidity": data["main"]["humidity"],
                        "wind_speed": data["wind"]["speed"],
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_msg = f"Weather API error: {response.status}"
                    logger.error(error_msg)
                    return {"error": error_msg}
                    
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return {"error": str(e)}
    
    # ==================== STOCKS ====================
    
    async def get_stock_price(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Get current stock price
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Stock data
        """
        try:
            await self._ensure_session()
            
            # Using Alpha Vantage API
            if not self.alpha_vantage_key:
                logger.warning("No Alpha Vantage API key, returning mock data")
                return {
                    "symbol": symbol,
                    "price": 150.25,
                    "change": 2.15,
                    "change_percent": 1.45,
                    "volume": 50000000,
                    "description": f"Mock stock data for {symbol}"
                }
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        return {
                            "symbol": quote["01. symbol"],
                            "price": float(quote["05. price"]),
                            "change": float(quote["09. change"]),
                            "change_percent": quote["10. change percent"].rstrip('%'),
                            "volume": int(quote["06. volume"]),
                            "timestamp": quote["07. latest trading day"]
                        }
                    else:
                        return {"error": "Invalid symbol or API limit reached"}
                else:
                    return {"error": f"Stock API error: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Stock fetch error: {e}")
            return {"error": str(e)}
    
    async def get_crypto_price(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Get cryptocurrency price
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Crypto price data
        """
        try:
            await self._ensure_session()
            
            # Using CoinGecko API (no key required)
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDT': 'tether',
                'BNB': 'binancecoin',
                'SOL': 'solana'
            }
            
            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if coin_id in data:
                        coin_data = data[coin_id]
                        return {
                            "symbol": symbol.upper(),
                            "price": coin_data["usd"],
                            "change_24h": coin_data.get("usd_24h_change", 0),
                            "volume_24h": coin_data.get("usd_24h_vol", 0),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": "Invalid crypto symbol"}
                else:
                    return {"error": f"Crypto API error: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Crypto fetch error: {e}")
            return {"error": str(e)}
    
    # ==================== NEWS ====================
    
    async def get_news(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get latest news articles
        
        Args:
            query: Search query
            limit: Number of articles
            
        Returns:
            News articles
        """
        try:
            await self._ensure_session()
            
            # Using NewsAPI
            if not self.news_api_key:
                logger.warning("No news API key, returning mock data")
                return {
                    "query": query,
                    "articles": [
                        {
                            "title": f"Mock news article about {query}",
                            "description": "This is mock news data",
                            "source": "Mock Source",
                            "published": datetime.now().isoformat()
                        }
                    ]
                }
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": self.news_api_key,
                "pageSize": limit,
                "sortBy": "publishedAt",
                "language": "en"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = []
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article["title"],
                            "description": article.get("description", ""),
                            "source": article["source"]["name"],
                            "url": article["url"],
                            "published": article["publishedAt"]
                        })
                    
                    return {
                        "query": query,
                        "total_results": data.get("totalResults", 0),
                        "articles": articles
                    }
                else:
                    return {"error": f"News API error: {response.status}"}
                    
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return {"error": str(e)}
    
    # ==================== WEB SEARCH ====================
    
    async def web_search(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Perform web search
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            Search results
        """
        try:
            await self._ensure_session()
            
            # Using DuckDuckGo Instant Answer API (no key required)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    
                    # Abstract (summary)
                    if data.get("Abstract"):
                        results.append({
                            "type": "summary",
                            "title": data.get("Heading", query),
                            "content": data["Abstract"],
                            "url": data.get("AbstractURL", "")
                        })
                    
                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:limit]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append({
                                "type": "result",
                                "title": topic.get("Text", "").split(" - ")[0],
                                "content": topic.get("Text", ""),
                                "url": topic.get("FirstURL", "")
                            })
                    
                    return {
                        "query": query,
                        "results": results
                    }
                else:
                    return {"error": f"Search API error: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {"error": str(e)}