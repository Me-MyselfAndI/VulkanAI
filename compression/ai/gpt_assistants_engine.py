import json
import math
import random
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import openai
import waiting
import yaml


def generate_product_file(products, file_code=None):
    if file_code is None:
        file_code = random.randint(0, 1000000)
    file_name = f'products-{file_code}.md'
    with open(f'compression/product_files/{file_name}', 'w') as file:
        file.write('| Item id | Description |\n| -- | -- |\n')
        for i, product in enumerate(products):
            file.write(f'| {i} | {product} |\n')

    return file_name


class GPTAssistantsEngine:
    def __init__(self, api_key=None, org_url=None, verbose=0):
        self.verbose = verbose
        if (api_key is None) != (org_url is None):
            if self.verbose >= 0:
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

    def get_response(self, prompt: str, file_data: ()):
        thread = self.client.beta.threads.create()

        product_file = {'file-name': generate_product_file(file_data)}
        try:
            product_file['gpt-object'] = self.client.files.create(
                file=open(f"compression/product_files/{product_file['file-name']}", 'rb'),
                purpose='assistants'
            )

        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33m'
                      f'Warning Raised by GPT while creating file:  {error}\n\t'
                      f'Request:  {product_file["file-name"]}'
                      f'\u001b[0m')
            return '0', error

        try:
            assistant = self.client.beta.assistants.create(
                model=self.model,
                instructions='You only answer in JSON where each item is matched with its response, formatted like '
                             '{"item id": "response"}, not anything on top of that. You always include one answer for '
                             'each item, and this answer must be a single number',
                tools=[{'type': 'retrieval'}],
                file_ids=[product_file['gpt-object'].id]
            )
        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33mWarning Raised by GPT when creating an assistant:  {error}\u001b[0m')

            self.client.files.delete(product_file['gpt-object'].id)

            return '0', error

        try:
            thread = self.client.beta.threads.create()
        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33m'
                      f'Warning Raised by GPT while creating thread:  {error}\u001b[0m')

            self.client.files.delete(product_file['gpt-object'].id)

        try:
            message = self.client.beta.threads.messages.create(
                role='user', content=prompt, thread_id=thread.id, file_ids=[product_file['gpt-object'].id]
            )
        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33m'
                      f'Warning Raised by GPT while creating message:  {error}\u001b[0m')

            self.client.files.delete(product_file['gpt-object'].id)
            self.client.beta.threads.delete(thread_id=thread.id)

        try:
            run = self.client.beta.threads.runs.create(
                assistant_id=assistant.id,
                thread_id=thread.id
            )
        except Exception as error:
            if self.verbose >= 1:
                print(f'\u001b[33m'
                      f'Warning Raised by GPT while creating/running thread:  {error}\u001b[0m')

            self.client.files.delete(product_file['gpt-object'].id)
            self.client.beta.threads.delete(thread_id=thread.id)

            return '0', error

        run_status = 'in_progress'

        def check_for_update():
            nonlocal run_status
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=run.thread_id,
                run_id=run.id
            ).status

            return run_status in ['completed', 'cancelled', 'failed', 'expired']

        waiting.wait(check_for_update, sleep_seconds=0.1)

        try:
            self.client.beta.assistants.files.delete(
                assistant_id=assistant.id,
                file_id=product_file['gpt-object'].id
            )
            self.client.files.delete(product_file['gpt-object'].id)
        except Exception as error:
            print(
                f"\u001b[31mMajor Warning! Could NOT delete a file. Go in and do manually to avoid incurring daily cost {error}")
            self.client.beta.threads.delete(thread_id=thread.id)

            return '0', error

        if run_status != 'completed':
            error_message = f'Warning! The GPT request could not execute properly. Run status: {run_status}'
            if self.verbose >= 1:
                print(f'\u001b[33m{error_message}\u001b[m')

            self.client.beta.threads.delete(thread_id=thread.id)
            self.client.beta.assistants.delete(assistant.id)

            return '0', error_message

        try:
            response = self.client.beta.threads.messages.list(thread.id).data[0].content[-1].text.value
        except Exception as error:
            if self.verbose >= 1:
                print(f"\u001b[33mWarning! GPT failed to retrieve the response. Exception: {error}")

            self.client.beta.threads.delete(thread_id=thread.id)
            self.client.beta.assistants.delete(assistant_id=assistant.id)
            return '0', error

        try:
            self.client.beta.threads.delete(thread.id)
        except Exception as error:
            if self.verbose >= 1:
                print(f"\u001b[33mWarning! Could NOT delete the thread: {error}")
            return '0', error

        try:
            self.client.beta.assistants.delete(assistant.id)
        except Exception as error:
            if self.verbose >= 1:
                print(f"\u001b[33mWarning! Could NOT delete the assistant: {error}")
            return '0', error

        return response.strip().strip("```").strip('json').strip('\n')

    def get_responses_async(self, prompt: str, args=(), batch_size=5, timeout=20):
        with ThreadPoolExecutor() as executor:
            futures = []
            batches = [
                args[i * batch_size: (i + 1) * batch_size]
                for i in range(math.ceil(len(args) / batch_size))
            ]
            for i, curr_batch in enumerate(batches):
                futures.append(
                    executor.submit(self.get_response, prompt, curr_batch)
                )

                sleep(0.02)  # Required to wait to avoid overloading the server

                if self.verbose >= 2:
                    print(f'\u001b[32mBatch {i}:\u001b[0m')
                    for j, product in enumerate(curr_batch):
                        print('\n\tPrompt', product)

            results = []
            for i in range(math.ceil(len(args) / batch_size)):
                try:
                    response = futures[i].result(timeout=timeout)
                except TimeoutError:
                    response = 0, f"Timeout happened - GPT couldn't return an answer in {timeout} seconds"

                json_response = json.loads(response)
                for key in range(len(batches[i])):
                    if str(key) in json_response:
                        try:
                            value = str(json_response[str(key)])
                        except Exception as error:
                            if self.verbose >= 1:
                                print(f"\u001b[33mCannot extract ranking of {key}: the returned value was faulty {value}. Error: {error}")

                        results.append()
                    else:
                        results.append('0')

            return results
