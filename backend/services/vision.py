# backend/services/vision.py
from openai import AsyncOpenAI
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VisionService:
    """Handle image analysis using GPT-4 Vision"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
        logger.info("Vision service initialized")
    
    async def analyze_image(
        self,
        image_data: str,
        prompt: str = "Describe this image in detail"
    ) -> str:
        """
        Analyze an image
        
        Args:
            image_data: Base64 encoded image
            prompt: Analysis instruction
            
        Returns:
            Analysis result as text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }],
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            logger.info(f"Image analyzed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            raise
    
    async def detect_objects(self, image_data: str) -> str:
        """Detect objects in image"""
        return await self.analyze_image(
            image_data,
            "List all objects visible in this image"
        )
    
    async def extract_text(self, image_data: str) -> str:
        """Extract text from image (OCR)"""
        return await self.analyze_image(
            image_data,
            "Extract all text visible in this image"
        )
    
    async def compare_images(
        self,
        image1_data: str,
        image2_data: str
    ) -> str:
        """Compare two images"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Compare these two images. What changed?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image1_data}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image2_data}"
                            }
                        }
                    ]
                }],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Image comparison error: {e}")
            raise