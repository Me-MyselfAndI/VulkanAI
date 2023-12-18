import math
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import openai
import yaml


class GPTEngine:
    def __init__(self, api_key=None, org_url=None):
        if (api_key is None) != (org_url is None):
            print('\u001b[31mOne of the keys for gpt was default while other was provided.'
                  'Either provide both GPT keys, or use both default')
            return

        if api_key is None:
            with open(r'keys\keys.yaml') as keys_file:
                keys = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['gpt-api']
                api_key = keys['api-url']
                org_url = keys['org-url']

        self.text_model = 'gpt-4-1106-preview'
        self.vision_model = 'gpt-4-vision-preview'
        self.client = openai.OpenAI(api_key=api_key, organization=org_url)

    def get_response(self, prompt: str, image_urls=None):
        if image_urls is None or not image_urls:
            model = self.text_model
            image_requests = []
        else:
            model = self.vision_model
            image_requests = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "low"
                    }
                }
                for url in image_urls
            ]
        text_request = [{
            "type": "text",
            "text": prompt
        }]

        full_request = [
                {
                    "role": "user",
                    "content": text_request + image_requests
                }
            ]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=full_request
            )
        except openai.BadRequestError as error:
            print(f'\u001b[33mWarning Raised by GPT:  {error}\n\tRequest:  {full_request}\u001b[0m')
            if error.code not in ['content_policy_violation', 'invalid_image_format']:
                raise Exception(error)
            return "1"

        return response.choices[0].message.content

    def get_responses_async(self, prompt: str, args=(), image_urls=None, batches=10, timeout=5):
        results = []
        if image_urls and (len(args) in (0, len(image_urls))):
            use_images = True
        else:
            use_images = False
            if image_urls:
                print("\u001b[33mWarning! Set of images doesn't correspond to the set of arguments! Skipping images!")

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(math.ceil(len(args) / batches)):
                curr_batch = args[i * batches: (i + 1) * batches]
                batch_requests = [prompt.format(product) for product in curr_batch]
                if use_images:
                    batch_images = image_urls[i * batches: (i + 1) * batches]
                    # Submit each request to the ThreadPoolExecutor
                    futures.extend(
                        executor.submit(self.get_response, request, image) for request, image in zip(batch_requests, batch_images)
                    )
                else:
                    futures.extend(
                        executor.submit(self.get_response, request) for request in batch_requests
                    )

                sleep(0.02)  # Required to wait to avoid overloading the server
                print(f'\u001b[32mBatch {i}:\u001b[0m')
                for j, product in enumerate(curr_batch):
                    print('\n\tPrompt', product)
                    if use_images:
                        print('\tImages', batch_images[j])

            # Retrieve results from futures
            for future in futures:
                try:
                    result = future.result(timeout=timeout)
                except TimeoutError:
                    result = 0, f"Timeout happened - GPT couldn't return an answer in {timeout} seconds"
                results.append(result)

        return results