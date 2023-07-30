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


# def asticaAPI(endpoint, payload, timeout):
#     response = requests.post(endpoint, data=json.dumps(payload), timeout=timeout,
#                              headers={'Content-Type': 'application/json', })
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return {'status': 'error', 'error': 'Failed to connect to the API.'}
#
# asticaAPI_key = 'YOUR API KEY'  # visit https://astica.ai
# asticaAPI_timeout = 35  # seconds  Using "gpt" or "gpt_detailed" will increase response time.
#
# asticaAPI_endpoint = 'https://vision.astica.ai/describe'
# asticaAPI_modelVersion = '2.1_full'  # '1.0_full', '2.0_full', or '2.1_full'
#
# # Input Method 1: https URL of a jpg/png image (faster)
# asticaAPI_input = 'https://www.astica.org/inputs/analyze_3.jpg'
#
# '''
# #Input Method 2: base64 encoded string of a local image (slower)
# path_to_local_file = 'image.jpg';
# with open(path_to_local_file, 'rb') as file:
#     image_data = file.read()
# image_extension = os.path.splitext(path_to_local_file)[1]
# #For now, let's make sure to prepend appropriately with: "data:image/extension_here;base64"
# asticaAPI_input = f"data:image/{image_extension[1:]};base64,{base64.b64encode(image_data).decode('utf-8')}"
# '''
#
# asticaAPI_visionParams = 'description'  # ,gpt,objects,faces'  # comma separated options; leave blank for all; note "gpt" and "gpt_detailed" are slow.
# '''
#     '1.0_full' supported options:
#         description
#         objects
#         categories
#         moderate
#         tags
#         brands
#         color
#         faces
#         celebrities
#         landmarks
#         gpt new (Slow - be patient)
#         gpt_detailed new (Much Slower)
#
#     '2.0_full' supported options:
#         description
#         objects
#         tags
#         describe_all new
#         text_read new
#         gpt new (Slow - be patient)
#         gpt_detailed new (Much Slower)
#
#     '2.1_full' supported options:
#         Supports all options
#
# '''
#
# # Define payload dictionary
# asticaAPI_payload = {
#     'tkn': asticaAPI_key,
#     'modelVersion': asticaAPI_modelVersion,
#     'visionParams': asticaAPI_visionParams,
#     'input': asticaAPI_input,
# }
#

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