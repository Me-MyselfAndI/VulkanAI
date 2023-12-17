import math
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from time import sleep

import requests
import json
import yaml


class AsticaEngine:
    def __init__(self, api_key=None, timeout=200):
        if api_key is None:
            with open(r'keys\keys.yaml') as keys_file:
                api_key = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['astica-api']
        self.api_key = api_key
        self.timeout = timeout
        self.endpoint = 'https://vision.astica.ai/describe'
        self.model_version = '2.1_full'

    def get_image_description(self, image_link):
        try:
            payload = {
                'tkn': self.api_key,
                'modelVersion': self.model_version,
                'visionParams': 'gpt',  # Available: 'gpt,description,objects,faces'
                'input': image_link,
            }

            response = requests.post(self.endpoint, data=json.dumps(payload), timeout=self.timeout,
                                     headers={'Content-Type': 'application/json', })
            if response.status_code == 200:
                return response.status_code, response.json().get('caption_GPTS', 'ERROR')
            return response.status_code, 'Failed to connect to the API.'
        except Exception as e:
            return 0, f'Crashed while interacting with Astica server - unclassified error {e}'

    def get_image_descriptions_async(self, images, batches=10, timeout=5):
        results = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(math.ceil(len(images) / batches)):
                curr_batch = images[i * batches: (i + 1) * batches]

                # Submit each request to the ThreadPoolExecutor
                futures.extend(
                    executor.submit(self.get_image_description, image) for image in curr_batch
                )

                sleep(0.02)  # Required wait to avoid overloading the server
                print(f'\u001b[32mAstica: batch {i}:\u001b[0m')
                for j, image in enumerate(curr_batch):
                    print('\n\t', j, image)

                # Retrieve results from futures
                for j, future in enumerate(futures):
                    try:
                        result = future.result(timeout=timeout)
                        print(f'Astica, batch {i}, image {j} - received result: {result}')
                    except TimeoutError:
                        result = 0, f"Timeout happened - Astica couldn't return an answer in {timeout} seconds"
                    results.append(result)

        return results

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
