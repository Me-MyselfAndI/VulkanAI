import math
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import anthropic
import yaml


class ClaudeEngine:
    def __init__(self, api_key=None, verbose=0, max_tokens=1000):
        self.verbose = verbose

        if api_key is None:
            # with open(r'/var/www/html/keys/keys.yaml') as keys_file: #Server Side
            with open(r'keys/keys.yaml') as keys_file:
                api_key = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['claude-api']

        self.cheap_model = 'claude-3-haiku-20240229'
        self.medium_model = 'claude-3-sonet-20240229'
        self.expensive_model = 'claude-3-opus-20240229'

        self.client = anthropic.Anthropic(api_key=api_key)
        self.max_tokens = max_tokens

    def get_response(self, prompt: str, model_type='expensive', image_urls=None):
        if image_urls is not None:
            if self.verbose >= 0:
                print(
                    "\u001b[31mImage support has not yet been implemented in Claude access point. Change the code\u001b[0m")
            raise Exception("Image support has not yet been implemented in Claude access point. Change the code")

        if model_type == 'cheap':
            model = self.cheap_model
        elif model_type == 'medium':
            model = self.medium_model
        elif model_type == 'expensive':
            model = self.expensive_model
        else:
            if self.verbose >= 1:
                print(f'\u001b[31mError encountered upon Claude request generation: model type was {model_type}. '
                      f'Choose from "cheap", "medium", "expensive"\u001b[0m')
            raise Exception(f'Error encountered upon Claude request generation: model type was {model_type}. '
                            f'Choose from "cheap", "medium", "expensive"')

        full_request = [
            {'role': 'user', 'content': prompt}
        ]

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=self.max_tokens,
                messages=full_request
            )
        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33mWarning Raised by Claude:  {error}\n\tRequest:  {full_request}\u001b[0m')
            return "1"

        result = response.content[0].text
        return result.strip().strip('\n')

    def get_responses_async(self, prompt: str, args=(), image_urls=None, batches=10, timeout=10, use_cheap_model=False):
        results = []
        if image_urls and (len(args) in (0, len(image_urls))):
            use_images = True
        else:
            use_images = False
            if image_urls:
                if self.verbose >= 0:
                    print("\u001b[33mWarning! Set of images doesn't correspond to the set of arguments! Skipping "
                          "images!\u001b[0m")

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(math.ceil(len(args) / batches)):
                curr_batch = args[i * batches: (i + 1) * batches]
                batch_requests = [prompt.format(product) for product in curr_batch]
                if use_images:
                    batch_images = image_urls[i * batches: (i + 1) * batches]
                    # Submit each request to the ThreadPoolExecutor
                    futures.extend(
                        executor.submit(self.get_response, request, 'cheap' if use_cheap_model else 'expensive', image)
                        for request, image in zip(batch_requests, batch_images)
                    )
                else:
                    futures.extend(
                        executor.submit(self.get_response, request, 'cheap' if use_cheap_model else 'expensive') for
                        request in batch_requests
                    )

                sleep(0.02)  # Required to wait to avoid overloading the server

                if self.verbose >= 2:
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
