"""
YouTube video transcript loading utilities.

This module provides utilities for loading YouTube video transcripts
with enhanced error handling, metadata extraction, and content formatting.
"""

from pathlib import Path
from typing import List, Union, Optional
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import pytube

from .base import DocumentLoader
from ..models import Document, DocumentType, YouTubeVideo, YouTubeProcessingError


class YouTubeLoader(DocumentLoader):
    """
    Load YouTube video transcripts and metadata.
    
    Extracts video transcripts, handles multiple languages,
    and provides comprehensive video metadata.
    """

    def __init__(self, language_codes: Optional[List[str]] = None):
        """
        Initialize the YouTube loader.
        
        Args:
            language_codes: Preferred language codes for transcripts (e.g., ['en', 'es'])
        """
        super().__init__()
        self.language_codes = language_codes or ['en']
        self.formatter = TextFormatter()

    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if this loader can handle the given source.
        
        Args:
            source: URL or string to check
            
        Returns:
            True if the source is a YouTube URL, False otherwise
        """
        if isinstance(source, Path):
            return False
        
        return self._is_youtube_url(str(source))

    def load_documents(self, source: Union[Path, str]) -> List[Document]:
        """
        Load documents from the given YouTube URL.
        
        Args:
            source: YouTube URL to load from
            
        Returns:
            List containing a single Document object with video transcript
            
        Raises:
            YouTubeProcessingError: If loading fails
        """
        if not self.can_load(source):
            raise YouTubeProcessingError(f"Invalid YouTube URL: {source}")
        
        try:
            video_id = self._extract_video_id(str(source))
            youtube_video = self._load_youtube_video(video_id, str(source))
            document = self._create_document_from_video(youtube_video)
            
            return [document]
            
        except Exception as e:
            raise YouTubeProcessingError(f"Failed to load YouTube video {source}: {e}")

    def _is_youtube_url(self, url: str) -> bool:
        """
        Check if a URL is a valid YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if it's a YouTube URL, False otherwise
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        
        return False

    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID string
            
        Raises:
            YouTubeProcessingError: If video ID cannot be extracted
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise YouTubeProcessingError(f"Could not extract video ID from URL: {url}")

    def _load_youtube_video(self, video_id: str, url: str) -> YouTubeVideo:
        """
        Load YouTube video data including transcript and metadata.
        
        Args:
            video_id: YouTube video ID
            url: Original URL
            
        Returns:
            YouTubeVideo object with complete data
            
        Raises:
            YouTubeProcessingError: If video cannot be loaded
        """
        try:
            # Get transcript
            transcript_text, language_used = self._get_transcript(video_id)
            
            # Get video metadata using pytube
            video_metadata = self._get_video_metadata(url)
            
            return YouTubeVideo(
                video_id=video_id,
                title=video_metadata.get('title', 'Unknown Title'),
                duration=video_metadata.get('duration', 0),
                channel=video_metadata.get('channel', 'Unknown Channel'),
                transcript=transcript_text,
                url=url,
                language=language_used,
                view_count=video_metadata.get('view_count'),
                upload_date=video_metadata.get('upload_date'),
            )
            
        except Exception as e:
            raise YouTubeProcessingError(f"Failed to load YouTube video {video_id}: {e}")

    def _get_transcript(self, video_id: str) -> tuple[str, str]:
        """
        Get transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (transcript_text, language_code)
            
        Raises:
            YouTubeProcessingError: If transcript cannot be retrieved
        """
        try:
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Get list of available transcripts
            transcript_list = api.list(video_id)
            
            # First try manually created transcripts in preferred languages
            for lang_code in self.language_codes:
                try:
                    transcript = transcript_list.find_manually_created_transcript([lang_code])
                    transcript_data = transcript.fetch()
                    formatted_text = self.formatter.format_transcript(transcript_data)
                    return formatted_text, lang_code
                except:
                    continue
            
            # Then try auto-generated transcripts in preferred languages
            for lang_code in self.language_codes:
                try:
                    transcript = transcript_list.find_generated_transcript([lang_code])
                    transcript_data = transcript.fetch()
                    formatted_text = self.formatter.format_transcript(transcript_data)
                    return formatted_text, lang_code
                except:
                    continue
            
            # Finally, try any available transcript
            try:
                # Get the first available transcript
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    transcript = available_transcripts[0]
                    transcript_data = transcript.fetch()
                    formatted_text = self.formatter.format_transcript(transcript_data)
                    return formatted_text, transcript.language_code
            except:
                pass
            
            raise YouTubeProcessingError(f"No transcript available for video {video_id}")
            
        except Exception as e:
            raise YouTubeProcessingError(f"Failed to get transcript for video {video_id}: {e}")

    def _get_video_metadata(self, url: str) -> dict:
        """
        Get video metadata using pytube.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video metadata
        """
        metadata = {}
        
        try:
            yt = pytube.YouTube(url)
            
            metadata.update({
                'title': yt.title or 'Unknown Title',
                'channel': yt.author or 'Unknown Channel',
                'duration': yt.length or 0,
                'view_count': yt.views,
                'upload_date': yt.publish_date.isoformat() if yt.publish_date else None,
                'description': yt.description or '',
                'keywords': yt.keywords or [],
                'rating': getattr(yt, 'rating', None),
            })
            
        except Exception as e:
            print(f"Warning: Failed to get video metadata: {e}")
            # Provide defaults
            metadata.update({
                'title': 'Unknown Title',
                'channel': 'Unknown Channel',
                'duration': 0,
                'view_count': None,
                'upload_date': None,
                'description': '',
                'keywords': [],
                'rating': None,
            })
        
        return metadata

    def _create_document_from_video(self, youtube_video: YouTubeVideo) -> Document:
        """
        Create a Document object from YouTube video data.
        
        Args:
            youtube_video: YouTubeVideo object
            
        Returns:
            Document object with formatted content and metadata
        """
        # Format content with video information and transcript
        content_parts = [
            f"=== YouTube Video: {youtube_video.title} ===",
            f"Channel: {youtube_video.channel}",
            f"Duration: {youtube_video.get_duration_formatted()}",
            f"URL: {youtube_video.url}",
            "",
            "=== Transcript ===",
            youtube_video.transcript
        ]
        
        content = "\n".join(content_parts)
        
        # Create comprehensive metadata
        metadata = {
            "video_id": youtube_video.video_id,
            "video_title": youtube_video.title,
            "channel_name": youtube_video.channel,
            "duration_seconds": youtube_video.duration,
            "duration_formatted": youtube_video.get_duration_formatted(),
            "language": youtube_video.language,
            "view_count": youtube_video.view_count,
            "upload_date": youtube_video.upload_date,
            "source_url": youtube_video.url,
            "content_type": "youtube_transcript",
            "transcript_word_count": len(youtube_video.transcript.split()),
            "transcript_char_count": len(youtube_video.transcript),
        }
        
        return Document(
            content=content,
            metadata=metadata,
            source_path=None,
            document_type=DocumentType.YOUTUBE,
            document_id=self.generate_document_id()
        )

    def load_multiple_videos(self, urls: List[str]) -> List[Document]:
        """
        Load multiple YouTube videos.
        
        Args:
            urls: List of YouTube URLs
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for url in urls:
            try:
                video_documents = self.load_documents(url)
                documents.extend(video_documents)
            except Exception as e:
                print(f"Warning: Failed to load video {url}: {e}")
                continue
        
        return documents

    def detect_youtube_urls(self, text: str) -> List[str]:
        """
        Detect YouTube URLs in text.
        
        Args:
            text: Text to search for YouTube URLs
            
        Returns:
            List of detected YouTube URLs
        """
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+(?:\S*)?',
            r'https?://(?:www\.)?youtu\.be/[a-zA-Z0-9_-]+(?:\S*)?',
            r'https?://(?:www\.)?youtube\.com/embed/[a-zA-Z0-9_-]+(?:\S*)?',
            r'https?://(?:www\.)?youtube\.com/v/[a-zA-Z0-9_-]+(?:\S*)?',
        ]
        
        urls = []
        for pattern in youtube_patterns:
            matches = re.findall(pattern, text)
            urls.extend(matches)
        
        return list(set(urls))  # Remove duplicates

    def get_video_info(self, url: str) -> dict:
        """
        Get basic video information without loading transcript.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with basic video info
        """
        try:
            video_id = self._extract_video_id(url)
            metadata = self._get_video_metadata(url)
            
            return {
                "video_id": video_id,
                "title": metadata.get('title', 'Unknown'),
                "channel": metadata.get('channel', 'Unknown'),
                "duration": metadata.get('duration', 0),
                "duration_formatted": self._format_duration(metadata.get('duration', 0)),
                "url": url,
                "view_count": metadata.get('view_count'),
                "upload_date": metadata.get('upload_date'),
            }
            
        except Exception as e:
            raise YouTubeProcessingError(f"Failed to get video info for {url}: {e}")

    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to HH:MM:SS or MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
