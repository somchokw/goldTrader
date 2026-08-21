import os
from google import genai
from pydantic import BaseModel, Field
import json
import logging
from config import GEMINI_API_KEY
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

from typing import Optional

class OrderDetails(BaseModel):
    entry_price: Optional[float] = Field(None, description="The entry price of the order. Null if not found.")
    current_price: Optional[float] = Field(None, description="The current price of the asset. Null if not found.")
    take_profit: Optional[float] = Field(None, description="The take profit (TP) price. Null if not set or not found.")
    stop_loss: Optional[float] = Field(None, description="The stop loss (SL) price. Null if not set or not found.")
    action: Optional[str] = Field(None, description="The order direction: 'BUY' or 'SELL'. Null if not found.")
    order_status: str = Field("ACTIVE", description="The status of the order: 'ACTIVE' (currently running/executed) or 'PENDING' (limit/stop order waiting to execute). Default to ACTIVE if unknown.")

def extract_order_from_image(image_bytes: bytes) -> OrderDetails:
    """
    Extracts trading order details (Entry, Current Price, TP, SL, Status) from a screenshot.
    """
    candidate_models = [
        os.environ.get("VISION_MODEL", "gemini-2.5-flash"),
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-flash-latest"
    ]
    models_to_try = []
    for m in candidate_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    client = genai.Client(api_key=GEMINI_API_KEY)
    img = Image.open(BytesIO(image_bytes))
    
    prompt = (
        "Analyze this trading terminal screenshot (like MT4/MT5/TradingView). "
        "Extract the following values for the order:\n"
        "- Entry Price\n"
        "- Current Market Price\n"
        "- Take Profit (TP) price (if not set, return 0.0)\n"
        "- Stop Loss (SL) price (if not set, return 0.0)\n"
        "- The action (BUY or SELL)\n"
        "- The status of the order (ACTIVE if it's currently running, PENDING if it's a Buy/Sell Limit or Stop order)\n\n"
        "Return the data strictly in the requested JSON schema."
    )
    
    last_err = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[img, prompt],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': OrderDetails,
                    'temperature': 0.1,
                },
            )
            data = json.loads(response.text)
            return OrderDetails(**data)
        except Exception as e:
            last_err = e
            logger.warning(f"Vision model {model_name} failed: {e}. Trying fallback model...")
            continue
            
    logger.error(f"Error extracting data from image (all models failed): {last_err}")
    raise last_err
