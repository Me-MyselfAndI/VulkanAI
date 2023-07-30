import requests
import json
import base64
import os

class AsticaEngine:
    def __init__(self, api_key, timeout=200):
        self.api_key = api_key
        self.timeout = timeout
        self.endpoint = 'https://vision.astica.ai/describe'
        self.model_version = '2.1_full'

    def describe_image(self, image_link):
        payload = {
            'tkn': self.api_key,
            'modelVersion': self.model_version,
            'visionParams': 'gpt',      # 'gpt,description,objects,faces'
            'input': image_link,
        }

        response = requests.post(self.endpoint, data=json.dumps(payload), timeout=self.timeout,
                                 headers={'Content-Type': 'application/json', })
        if response.status_code == 200:
            return response.status_code, response.json()
        return response.status_code, {'error': 'Failed to connect to the API.'}

def main():
    api_key = 'B8757667-43F8-42A9-83B0-43E53FAA5224CD725B78-7776-4EA2-873A-946831E2F562'
    image_address = 'https://images-na.ssl-images-amazon.com/images/I/71rlMBf3vcL._AC_UL150_SR150,150_.jpg'

    astica_engine = AsticaEngine(api_key)
    # Call API function and store result
    response_status, result = astica_engine.describe_image(image_address)

    print('\nAstica API Output:')
    print(json.dumps(result, indent=4))
    print('=================')
    print('=================')

    # Handle asticaAPI response
    if 'status' in result:
        # Output Error if exists
        if result['status'] == 'error':
            print('Output:\n', result['error'])
        # Output Success if exists
        if result['status'] == 'success':
            if 'caption_GPTS' in result and result['caption_GPTS'] != '':
                print('=================')
                print('GPT Caption:', result['caption_GPTS'])
            if 'caption' in result and result['caption']['text'] != '':
                print('=================')
                print('Caption:', result['caption']['text'])
            if 'CaptionDetailed' in result and result['CaptionDetailed']['text'] != '':
                print('=================')
                print('CaptionDetailed:', result['CaptionDetailed']['text'])
            if 'objects' in result:
                print('=================')
                print('Objects:', result['objects'])
    else:
        print('Invalid response')


if __name__ == "__main__":
    main()