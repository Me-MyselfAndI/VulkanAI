import math
from time import sleep

import openai
from multiprocessing.pool import Pool
import yaml


class GPTEngine:
    def __init__(self, api_key=None, org_url=None):
        if (api_key is None) != (org_url is None):
            print('\u001b[31mOne of the keys for gpt was default while other was provided.'
                  'Either provide both GPT keys, or use both default')
            return

        if api_key is None:
            with open(r'keys\keys.yaml') as keys_file:
                api_key = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['gpt-api']['api-url']
                org_url = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']['gpt-api']['org-url']

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

    def get_responses_async(self, prompt: str, args=(), batches=5):
        pool = Pool()
        results = []
        for i in range(math.ceil(len(args) / batches)):
            curr_batch = args[i: i + batches + 1]
            results.extend(
                pool.imap(self.get_response, [
                    prompt.format(product) for product in curr_batch
                ])
            )
            sleep(0.02)  # Required to wait to avoid maxing out our server capacity
            print(f'\u001b[32mBatch {i}:\u001b[0m')
            for j in range(batches):
                print('\n\t', j, curr_batch[j])
        return results


def main():
    from compression.scraping.parser import Parser
    import yaml
    threshold = 3

    html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Filtered Website</title>
            <style>
                .products {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    justify-content: center;
                }
                .product {
                    border: 1px solid #ddd;
                    padding: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    width: 150px;
                    text-align: center;
                }
                .product img {
                    max-width: 100%;
                    max-height: 100px;
                }
            </style>
        </head>
        <body>
        <div class="products">
    """

    with open(r'..\..\compression\scraping\test.html', encoding='utf-8') as file:
        parser = Parser(html=file)

    with open(r'..\..\keys\keys.yaml') as keys_file:
        keys = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']

    parsed_result = parser.find_text_content()
    print('Text Content:\n\t', parsed_result)
    gpt = GPTEngine(keys['gpt-api']['api-url'], keys['gpt-api']['org-url'])

    for i, element in enumerate(parsed_result):
        request = ('I am looking for a way to remove dirt specs from a very old black and white video using '
                    'DaVinci Resolve 18. I am planning to change a text on this topic to make it more concise - as '
                    'concise as humanly possible without losing meaning. Tell me if I should keep this or remove if my '
                    'user only cares about reading the meaning of this article? Rate relevance of this from 1 to 5 where '
                    '1 is completely irrelevant and 5 is spot-on answer to the question. Just return the number, '
                    'nothing else' + element['text'])
        response = gpt.get_response(request)
        print(i, response, '\n\t', element['text'])
        if not '1' <= response <= '5':
            print(f"\u001b[31mWARNING! BAD RESPONSE: {response}")
            continue

        if int(response) >= threshold:
            html_content += f"""
            <div>
                {element['tag']}
            </div>
            """

    html_content += """
            </div>
        </body>
        </html>
        """

    with open("../../test_output_websites/filtered_website.html", "w") as file:
        file.write(html_content)

    print("Website generated: ../../test_output_websites/filtered_website.html")


if __name__ == '__main__':
    main()
