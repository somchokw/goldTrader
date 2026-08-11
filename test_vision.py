import asyncio
from vision import extract_order_from_image

async def main():
    with open('/Users/studiotwist/.gemini/antigravity/brain/c9e80eb0-0ae1-4df5-97cb-f8a916328d42/.user_uploaded/media_1786418596029.png', 'rb') as f:
        data = f.read()
    try:
        res = extract_order_from_image(data)
        print("Success:")
        print(res)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    asyncio.run(main())
