import openai


class GPTEngine:
    def __init__(self, api_url, org_url):
        openai.organization = org_url
        openai.api_key = api_url

        openai.Model.list()

        self.model = 'gpt-4'

    def get_response(self, prompt: str, *args):
        # Use {} and str.format() for arguments. For example:
        # prompt = "Hello, my name is {}, I work at {}"
        # args = ["Harvey", "DreamWave"]
        request = prompt.format(args)

        result = openai.ChatCompletion.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": request
            }]
        )

        return result.choices[0].message.content
