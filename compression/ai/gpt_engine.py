import math
from time import sleep

import openai
from multiprocessing.pool import Pool


class GPTEngine:
    def __init__(self, api_key, org_url):
        self.org_url = org_url
        self.api_key = api_key

        self.model = 'gpt-4'

    def get_response(self, prompt: str):
        openai.api_key = self.api_key
        openai.organization = self.org_url

        result = openai.ChatCompletion.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return result.choices[0].message.content

    def get_responses_async(self, prompt: str, args=(), batches=5):
        pool = Pool()
        results = []
        for i in range(math.ceil(len(args) / batches)):
            curr_batch = args[i : i + batches + 1]
            results.extend(
                pool.imap(self.get_response, [
                    prompt.format(product) for product in curr_batch
                ])
            )
            sleep(0.02)    # Required to wait to avoid maxing out our server capacity
            print(f'\u001b[32mBatch {i}:\u001b[0m')
            for j in range(batches):
                print('\n\t', j, curr_batch[j])
        return results
