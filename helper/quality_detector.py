import re
from typing import Dict, Optional, Tuple

# Quality patterns and their priority (lower = higher priority in display)
QUALITY_PATTERNS = {
    '480p': (r'480p', 1),
    '720p': (r'720p', 2),
    '1080p': (r'1080p', 3),
    'HDRip': (r'HDRip|HD-Rip|HD Rip', 4),
    '4K': (r'4K|2160p', 5),
    '360p': (r'360p', 0),
}

def extract_quality(filename: str) -> Optional[str]:
    """Extract quality tag from filename"""
    filename_upper = filename.upper()
    
    for quality, (pattern, _) in QUALITY_PATTERNS.items():
        if re.search(pattern, filename, re.IGNORECASE):
            return quality
    
    return None

def get_base_name(filename: str) -> str:
    """
    Remove quality tags, episode info, and extension to get base name
    Example: "Movie.Name.S01E01.1080p.mkv" -> "Movie.Name"
    """
    # Remove extension
    name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Replace separators with spaces to match word boundaries
    # Replace dots, underscores, dashes, slashes, colons, semicolons, commas
    name = re.sub(r'[.\-_/;:,\\]+', ' ', name)
    
    # Remove quality tags
    for quality, (pattern, _) in QUALITY_PATTERNS.items():
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove common patterns
    patterns_to_remove = [
        r'S\d+E\d+',  # Season/Episode
        r'\bS\d+\b',  # S01, S02 (Standalone)
        r'Season\s*\d+',
        r'Episode\s*\d+',
        r'\d{4}',  # Year
        r'BluRay|BRRip|WEBRip|WEB-DL',
        r'x264|x265|HEVC',
        r'\bDual\b',          # Dual
        r'\bAudio\b',         # Audio
        r'\bMulti\b',         # Multi
        r'\bmkv\b',           # mkv
        r'\bmp4\b',           # mp4
        r'\bavi\b',           # avi
        r'\[.*?\]',  # Brackets
        r'\(.*?\)',  # Parentheses
    ]
    
    for pattern in patterns_to_remove:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Clean up extra dots, dashes, spaces
    name = re.sub(r'[.\-_]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def get_series_name(filename: str) -> str:
    """
    Get series name by removing episode info more aggressively
    Example: "E07 Ancient Magus" -> "Ancient Magus"
    """
    name = get_base_name(filename)
    
    # Remove standalone episode numbers/patterns that get_base_name might miss
    patterns = [
        r'\bE\d+\b',              # E07, E1
        r'\bEp\d+\b',             # Ep07
        r'\bEpisode\s*\d+\b',     # Episode 07
        r'^\d+\s+',               # "07 Ancient Magus" (Start of string)
        r'\s+\d+$'                # "Ancient Magus 07" (End of string)
    ]
    
    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Cleanup
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_quality_priority(quality: str) -> int:
    """Get sort priority for quality"""
    return QUALITY_PATTERNS.get(quality, (None, 999))[1]

def parse_episode_info(filename: str) -> Dict:
    """Extract season and episode info"""
    info = {'season': None, 'episode': None}
    
    # Match S01E01, S01-E01, S01_E01 formats
    match = re.search(r'S(\d+)[._-]*E(\d+)', filename, re.IGNORECASE)
    if match:
        info['season'] = int(match.group(1))
        info['episode'] = int(match.group(2))
    
    return info

def should_group_files(file1: str, file2: str) -> bool:
    """Check if two files should be grouped together"""
    base1 = get_base_name(file1)
    base2 = get_base_name(file2)
    
    # Must have same base name
    if base1.lower() != base2.lower():
        return False
    
    # Must have different qualities
    quality1 = extract_quality(file1)
    quality2 = extract_quality(file2)
    
    if not quality1 or not quality2:
        return False
    
    return quality1 != quality2
