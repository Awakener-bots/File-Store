"""
Payment Gateway Integration for Credit Purchase System

Supports multiple payment methods:
1. Manual Payment (Screenshot verification)
2. Telegram Stars (Built-in Telegram payment)
3. Razorpay (For India - UPI, Cards, Wallets)
4. PayTM (Alternative for India)
"""

from typing import Optional, Dict
import secrets
import hashlib
from datetime import datetime


class PaymentHandler:
    """Base payment handler class"""
    
    def __init__(self, config: dict):
        self.config = config
        self.pending_payments = {}  # In-memory storage for pending payments
    
    async def create_payment(self, user_id: int, package: dict) -> dict:
        """Create a payment request. Returns payment details."""
        raise NotImplementedError
    
    async def verify_payment(self, payment_id: str) -> dict:
        """Verify payment status. Returns verification result."""
        raise NotImplementedError


class ManualPaymentHandler(PaymentHandler):
    """Manual payment verification by admin"""
    
    async def create_payment(self, user_id: int, package: dict) -> dict:
        payment_id = f"MANUAL_{user_id}_{secrets.token_hex(4)}"
        
        self.pending_payments[payment_id] = {
            "user_id": user_id,
            "package": package,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        return {
            "payment_id": payment_id,
            "method": "manual",
            "instructions": (
                f"💰 **Payment Instructions**\n\n"
                f"**Package**: {package['credits']} Credits\n"
                f"**Price**: ₹{package['price']}\n\n"
                f"**Payment Methods**:\n"
                f"• UPI: {self.config.get('upi_id', 'your-upi@bank')}\n"
                f"• Phone Pay/Google Pay: {self.config.get('phone', 'XXXXXXXXXX')}\n\n"
                f"**Steps**:\n"
                f"1. Send payment to above UPI/Phone\n"
                f"2. Take screenshot of payment\n"
                f"3. Send screenshot to admin\n"
                f"4. Wait for verification\n\n"
                f"**Payment ID**: `{payment_id}`\n"
                f"(Share this ID with admin)"
            )
        }
    
    async def verify_payment(self, payment_id: str) -> dict:
        """Admin manually verifies payment"""
        payment = self.pending_payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}
        
        return {
            "success": True,
            "user_id": payment["user_id"],
            "package": payment["package"],
            "payment_id": payment_id
        }
    
    async def approve_payment(self, payment_id: str):
        """Admin approves payment"""
        if payment_id in self.pending_payments:
            self.pending_payments[payment_id]["status"] = "approved"
    
    async def reject_payment(self, payment_id: str):
        """Admin rejects payment"""
        if payment_id in self.pending_payments:
            self.pending_payments[payment_id]["status"] = "rejected"


class TelegramStarsHandler(PaymentHandler):
    """Telegram Stars payment (built-in Telegram payment)"""
    
    async def create_payment(self, user_id: int, package: dict) -> dict:
        payment_id = f"STARS_{user_id}_{secrets.token_hex(4)}"
        
        # Telegram Stars pricing (1 Star ≈ ₹1)
        stars_price = package['price']
        
        return {
            "payment_id": payment_id,
            "method": "telegram_stars",
            "stars_amount": stars_price,
            "package": package,
            "instructions": (
                f"⭐ **Pay with Telegram Stars**\n\n"
                f"**Package**: {package['credits']} Credits\n"
                f"**Price**: {stars_price} Stars\n\n"
                f"Click the button below to pay with Telegram Stars"
            )
        }
    
    async def verify_payment(self, payment_id: str) -> dict:
        """Telegram automatically verifies Stars payment"""
        # This will be handled by Telegram's payment callback
        return {"success": True, "payment_id": payment_id}


class RazorpayHandler(PaymentHandler):
    """Razorpay payment gateway (India)"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get('razorpay_key')
        self.api_secret = config.get('razorpay_secret')
    
    async def create_payment(self, user_id: int, package: dict) -> dict:
        """Create Razorpay payment link"""
        payment_id = f"RAZORPAY_{user_id}_{secrets.token_hex(4)}"
        
        # In production, you would call Razorpay API here
        # For now, we'll return a mock payment link
        
        payment_link = f"https://razorpay.com/payment/{payment_id}"
        
        self.pending_payments[payment_id] = {
            "user_id": user_id,
            "package": package,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        return {
            "payment_id": payment_id,
            "method": "razorpay",
            "payment_link": payment_link,
            "instructions": (
                f"💳 **Pay with Razorpay**\n\n"
                f"**Package**: {package['credits']} Credits\n"
                f"**Price**: ₹{package['price']}\n\n"
                f"Click the button below to pay securely via Razorpay\n"
                f"(Supports UPI, Cards, Wallets)"
            )
        }
    
    async def verify_payment(self, payment_id: str) -> dict:
        """Verify Razorpay payment via webhook"""
        # In production, verify signature from Razorpay webhook
        payment = self.pending_payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}
        
        return {
            "success": True,
            "user_id": payment["user_id"],
            "package": payment["package"],
            "payment_id": payment_id
        }


class PaymentGateway:
    """Main payment gateway manager"""
    
    def __init__(self, config: dict):
        self.config = config
        self.method = config.get('payment_method', 'manual')
        
        # Initialize appropriate handler
        if self.method == 'manual':
            self.handler = ManualPaymentHandler(config)
        elif self.method == 'telegram_stars':
            self.handler = TelegramStarsHandler(config)
        elif self.method == 'razorpay':
            self.handler = RazorpayHandler(config)
        else:
            self.handler = ManualPaymentHandler(config)  # Default to manual
    
    async def create_payment(self, user_id: int, package: dict) -> dict:
        """Create payment request"""
        return await self.handler.create_payment(user_id, package)
    
    async def verify_payment(self, payment_id: str) -> dict:
        """Verify payment"""
        return await self.handler.verify_payment(payment_id)
    
    async def approve_payment(self, payment_id: str):
        """Approve manual payment (admin only)"""
        if isinstance(self.handler, ManualPaymentHandler):
            await self.handler.approve_payment(payment_id)
    
    async def reject_payment(self, payment_id: str):
        """Reject manual payment (admin only)"""
        if isinstance(self.handler, ManualPaymentHandler):
            await self.handler.reject_payment(payment_id)


# Credit packages configuration
DEFAULT_PACKAGES = [
    {"id": "pkg_10", "credits": 10, "price": 50, "currency": "INR"},
    {"id": "pkg_25", "credits": 25, "price": 100, "currency": "INR", "popular": True},
    {"id": "pkg_50", "credits": 50, "price": 180, "currency": "INR"},
    {"id": "pkg_100", "credits": 100, "price": 300, "currency": "INR"},
]


def get_package_by_id(package_id: str, packages: list = None) -> Optional[dict]:
    """Get package details by ID"""
    if packages is None:
        packages = DEFAULT_PACKAGES
    
    for pkg in packages:
        if pkg['id'] == package_id:
            return pkg
    return None
