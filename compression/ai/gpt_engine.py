import math
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

        self.model = 'gpt-4-1106-preview'
        self.client = openai.OpenAI(api_key=api_key, organization=org_url)

    def get_response(self, prompt: str):
        result = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return result.choices[0].message.content

    def get_responses_async(self, prompt: str, args=(), batches=10, timeout=5):
        results = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(math.ceil(len(args) / batches)):
                curr_batch = args[i * batches: (i + 1) * batches]
                requests = [prompt.format(product) for product in curr_batch]

                # Submit each request to the ThreadPoolExecutor
                futures.extend(
                    executor.submit(self.get_response, request) for request in requests
                )

                sleep(0.02)  # Required to wait to avoid overloading the server
                print(f'\u001b[32mBatch {i}:\u001b[0m')
                for j, product in enumerate(curr_batch):
                    print('\n\t', product)

            # Retrieve results from futures
            for future in futures:
                try:
                    result = future.result(timeout=timeout)
                except TimeoutError:
                    result = 0, f"Timeout happened - GPT couldn't return an answer in {timeout} seconds"
                results.append(result)

        return results
