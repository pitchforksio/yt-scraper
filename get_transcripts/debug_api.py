from youtube_transcript_api import YouTubeTranscriptApi

print("Attributes of YouTubeTranscriptApi:")
print(dir(YouTubeTranscriptApi))

try:
    print("\nAttempting to call get_transcript:")
    # Use a knon video ID
    print(YouTubeTranscriptApi.get_transcript("MwPzrPgxneU", languages=['en']))
except Exception as e:
    print(f"\nError: {e}")
