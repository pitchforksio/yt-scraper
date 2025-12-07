import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

print(f"Module file: {youtube_transcript_api.__file__}")

print(f"\nYouTubeTranscriptApi.fetch: {YouTubeTranscriptApi.fetch}")
print(f"YouTubeTranscriptApi.list: {YouTubeTranscriptApi.list}")

try:
    # Maybe it's list_transcripts?
    print(dir(YouTubeTranscriptApi.list_transcripts))
except:
    pass
