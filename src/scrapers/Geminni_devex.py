from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, UrlContext

client = genai.Client()
model_id = "gemini-2.5-flash"

tools = [
      {"url_context": {}},
      {"google_search": {}}
  ]

response = client.models.generate_content(
    model=model_id,
    contents="Give me three day events schedule based on YOUR_URL. Also let me know what needs to taken care of considering weather and commute.",
    config=GenerateContentConfig(
        tools=tools,
    )
)

for each in response.candidates[0].content.parts:
    print(each.text)
# get URLs retrieved for context
print(response.candidates[0].url_context_metadata)


prompt = """
Navigate to https://devex.com/funding/r. In the list Latest Funding Reports find the most recent (<=30 days) Devex procurement/tender/grant/open opportunity for video, photo, documentary, communications/multimedia/creative services.
Return:
•  reference number
•  title
•  published date
•  deadline
•  country
•  organization
•  short summary
•  URL
If nothing <=30 days, return the most recent you can find and note the date.
"""
