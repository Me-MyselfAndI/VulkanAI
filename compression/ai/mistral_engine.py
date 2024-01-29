import math
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

import yaml


class MistralEngine:
    def __init__(self, api_key=None, temperature=None, top_p=0.02, verbose=0):
        self.verbose = verbose
        self.temperature = temperature
        self.top_p = top_p

        if api_key is None:
            #with open(r'/var/www/html/keys/keys.yaml') as keys_file: #Server Side
            with open(r'keys/keys.yaml') as keys_file:
                api_key = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['mistral-api']

        self.model = 'mistral-medium'
        self.client = MistralClient(api_key=api_key)

    def get_response(self, prompt: str, max_tokens=None):
        try:
            response = self.client.chat(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                messages=[ChatMessage(role="user", content=prompt)]
            )
        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33mWarning Raised by Mistral:  {error}\n\tRequest:  {prompt}\u001b[0m')
            return "1"

        result = response.choices[0].message.content
        return result.strip().strip('\n')

    def get_responses_async(self, prompt: str, args=(), batches=2, timeout=1.1, max_tokens=None):
        results = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(math.ceil(len(args) / batches)):
                curr_batch = args[i * batches: (i + 1) * batches]
                batch_requests = [prompt.format(product) for product in curr_batch]
                futures.extend(
                    executor.submit(self.get_response, request, max_tokens) for request in batch_requests
                )

                sleep(0.02)  # Required to wait to avoid overloading the server

                if self.verbose >= 2:
                    print(f'\u001b[32mBatch {i}:\u001b[0m')
                    for j, product in enumerate(curr_batch):
                        print('\n\tPrompt', product)

            # Retrieve results from futures
            for future in futures:
                try:
                    result = future.result(timeout=timeout)
                except TimeoutError:
                    result = 0, f"Timeout happened - Mistral couldn't return an answer in {timeout} seconds"
                results.append(result)

        return results

def main():
    engine = MistralEngine(verbose=2)
    print(engine.get_response('Hello world'))

if __name__ == "__main__":
    main()