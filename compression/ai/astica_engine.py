import requests
import json


class AsticaEngine:
    def __init__(self, api_key, timeout=200):
        self.api_key = api_key
        self.timeout = timeout
        self.endpoint = 'https://vision.astica.ai/describe'
        self.model_version = '2.1_full'

    def get_image_description(self, image_link):
        payload = {
            'tkn': self.api_key,
            'modelVersion': self.model_version,
            'visionParams': 'gpt',  # Available: 'gpt,description,objects,faces'
            'input': image_link,
        }

        response = requests.post(self.endpoint, data=json.dumps(payload), timeout=self.timeout,
                                 headers={'Content-Type': 'application/json', })
        if response.status_code == 200:
            return response.status_code, response.json()['caption_GPTS']
        return response.status_code, 'Failed to connect to the API.'


def main():
    api_key = input("Enter Astica API key:\n")
    image_address = 'https://images-na.ssl-images-amazon.com/images/I/71rlMBf3vcL._AC_UL150_SR150,150_.jpg'

    astica_engine = AsticaEngine(api_key)
    # Call API function and store result
    response_status, result = astica_engine.get_image_description(image_address)

    print('=================')
    print('Astica API Output:')
    print(result)
    print('=================')


if __name__ == "__main__":
    main()
