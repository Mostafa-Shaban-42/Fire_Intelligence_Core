import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_whatsapp_alert(message: str, image_path: Optional[str] = None) -> bool:
    try:
        # WhatsApp/Twilio API Notification Logic Placeholder
        logger.info(f"WhatsApp Alert Sent: {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp alert: {e}")
        return False