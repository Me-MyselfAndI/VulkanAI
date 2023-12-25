import math
import urllib.request
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from time import sleep

import PIL
import google.generativeai as genai
import requests
import yaml


class GeminiEngine:
    def __init__(self, api_key=None, temperature=0.5):
        if api_key is None:
            with open(r'keys\keys.yaml') as keys_file:
                api_key = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['gemini-api']

        genai.configure(api_key=api_key)
        self.generation_config = genai.types.GenerationConfig(
            temperature=temperature
        )
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        self.text_model = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings,
                                                generation_config=self.generation_config)
        self.vision_model = genai.GenerativeModel('gemini-pro-vision', safety_settings=safety_settings,
                                                  generation_config=self.generation_config)

    def get_response(self, prompt: str, image_urls=None, temperature=None):
        if temperature is None:
            generation_config = self.generation_config
        try:
            if image_urls is None or not image_urls:
                model = self.text_model
                request = [prompt]
            else:
                model = self.vision_model
                request = [prompt]
                for url in image_urls:
                    img = requests.get(url)
                    request.append(PIL.Image.open(BytesIO(img.content)))
        except Exception as error:
            print(f"\u001b[33mWarning: image processing issue encountered for image {url}. Error: {error}\u001b[0m")
            return "1"
        try:
            response = model.generate_content(request, generation_config=generation_config)
        except Exception as error:
            if error.code == 429:
                sleep(1)
                try:
                    response = model.generate_content(request, generation_config=generation_config)
                    return response.text.strip()
                except Exception as error:
                    print(f'\u001b[33mWarning: Gemini failed to respond:  {error}\n\tRequest:  {request}\u001b[0m')
                    return "1"

        return response.text.strip()

    def get_responses_async(self, prompt: str, args=(), image_urls=None, batches=10, timeout=50, temperature=None):
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
                        executor.submit(self.get_response, request, image, temperature) for request, image in
                        zip(batch_requests, batch_images)
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
                    result = 0, f"Timeout happened - Gemini couldn't return an answer in {timeout} seconds"
                except Exception as e:
                    print(f"\u001b[31mAnother error encountered when waiting for response from Gemini: {e}\u001b[0m")
                results.append(result)

        return results
