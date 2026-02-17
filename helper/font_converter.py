"""
Small Caps Font Converter for Bot Messages
Converts regular text to small caps Unicode characters
"""

# Small caps character mapping
SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ',
    'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
    'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ',
    'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ',
    'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x',
    'Y': 'ʏ', 'Z': 'ᴢ'
}


def to_small_caps(text: str) -> str:
    """
    Convert text to small caps Unicode characters
    
    Args:
        text: Input text to convert
        
    Returns:
        Text with small caps characters
        
    Example:
        >>> to_small_caps("Hello World")
        'ʜᴇʟʟᴏ ᴡᴏʀʟᴅ'
    """
    return ''.join(SMALL_CAPS_MAP.get(char, char) for char in text)


def sc(text: str) -> str:
    """Shorthand for to_small_caps"""
    return to_small_caps(text)


# Pre-converted common phrases for better performance
COMMON_PHRASES = {
    "credits": "ᴄʀᴇᴅɪᴛꜱ",
    "balance": "ʙᴀʟᴀɴᴄᴇ",
    "earned": "ᴇᴀʀɴᴇᴅ",
    "spent": "ꜱᴘᴇɴᴛ",
    "expires": "ᴇxᴘɪʀᴇꜱ",
    "referrals": "ʀᴇғᴇʀʀᴀʟꜱ",
    "buy credits": "ʙᴜʏ ᴄʀᴇᴅɪᴛꜱ",
    "refer and earn": "ʀᴇғᴇʀ ᴀɴᴅ ᴇᴀʀɴ",
    "transactions": "ᴛʀᴀɴꜱᴀᴄᴛɪᴏɴꜱ",
    "payment": "ᴘᴀʏᴍᴇɴᴛ",
    "approved": "ᴀᴘᴘʀᴏᴠᴇᴅ",
    "pending": "ᴘᴇɴᴅɪɴɢ",
    "premium": "ᴘʀᴇᴍɪᴜᴍ",
    "file access": "ғɪʟᴇ ᴀᴄᴄᴇꜱꜱ",
    "checking subscription": "ᴄʜᴇᴄᴋɪɴɢ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ",
    "wait a sec": "ᴡᴀɪᴛ ᴀ ꜱᴇᴄ",
    "generating your link": "ɢᴇɴᴇʀᴀᴛɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ",
    "credit used": "ᴄʀᴇᴅɪᴛ ᴜꜱᴇᴅ",
    "remaining credits": "ʀᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛꜱ",
    "you earned": "ʏᴏᴜ ᴇᴀʀɴᴇᴅ",
    "get your file": "ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇ",
    "solve the shortener": "ꜱᴏʟᴠᴇ ᴛʜᴇ ꜱʜᴏʀᴛᴇɴᴇʀ",
    "bypass detected": "ʙʏᴘᴀꜱꜱ ᴅᴇᴛᴇᴄᴛᴇᴅ",
    "file will be deleted": "ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ",
    "your video file is successfully deleted": "ʏᴏᴜʀ ᴠɪᴅᴇᴏ ғɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ"
}


if __name__ == "__main__":
    # Test the converter
    test_phrases = [
        "Hello World",
        "Credits Balance",
        "You Earned 3 Credits!",
        "Checking subscription...",
        "BYPASS DETECTED"
    ]
    
    print("Small Caps Font Converter Test:\n")
    for phrase in test_phrases:
        print(f"{phrase} → {to_small_caps(phrase)}")
