import json


class Builder:
    _html_template_start = """
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>VulkanAI - Filtered Website</title>
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
    _html_template_end = """
                </div>
            </body>
            </html>
            """

    def __init__(self, llm, cheap_llm=None):
        self._llm = llm
        if cheap_llm is None:
            self._cheap_llm = self._llm
        else:
            self._cheap_llm = cheap_llm

    def generate_ancestral_html(self, html_tree, parsed_content, verbose=0):
        # Get ancestry that is to be kept:
        tags_to_keep = set()
        init_keep_tags = list(map(lambda x: x['tag'], parsed_content)) + html_tree.find_all('style') + html_tree.find_all('link')
        for item in init_keep_tags:
            curr_item = item
            tags_to_keep = tags_to_keep.union(set(curr_item.descendants))
            while curr_item not in tags_to_keep and curr_item is not None:
                tags_to_keep.add(curr_item)
                curr_item = curr_item.parent

        # Generate HTML that contains everything that needs to stay
        for tag in set(html_tree.find_all()).difference(tags_to_keep):
            # test_var = str(tags_to_keep)
            tag.extract()
            # if test_var != str(tags_to_keep):
            #     print("ERROR!!")

        return html_tree

    def generate_container_html(self, products, verbose=0):
        if len(products) == 0:
            return """
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>VulkanAI - Filtered Products</title>
                </head>
                <body>
                    No satisfying products could be found. Try toggling the threshold bar to loosen your requirements, or visit with a different prompt
                </body>
            </html>
            """

        html_content = self._html_template_start

        product_properties_filtered = self._cheap_llm.get_responses_async(
            "I have a list of some product's properties and values: {}. They got scrambled, and I can't tell if some "
            "of them are property names (i.e. 'price', 'color') or values (i.e. '$55', 'red'), or combinations (i.e. "
            "'price: $55' or 'color: red'). Return this exact list, but all property names removed. The remaining stuff"
            " is to be kept intact, in the exact order. Say nothing else, just return the list",
            [product['text'] for product in products],
            temperature=0.3
        )

        for i in range(len(products)):
            products[i]['text'] = product_properties_filtered[i]

        llm_product_property_responses = self._cheap_llm.get_responses_async(
            'This is a product with some properties I am giving you: {}. You must return me each property'
            'with its respective value, in the JSON format, nothing else. I am another bot and must be able to read '
            'your JSON without any extra efforts. If you can\'t, return 0 and nothing else',
            [product['text'] for product in products],
            temperature=0.3
        )

        product_properties_json = []
        for curr_product_properties in llm_product_property_responses:
            try:
                product_properties_json.append(json.loads(curr_product_properties.strip('```')))
            except ValueError as error:
                if verbose >= 1:
                    print(f"\u001b[33mWarning: jsonifying {curr_product_properties} yielded \"{error}\"\u001b[0m")
        for product, props in zip(products, product_properties_json):
            try:
                product_block = f"""
                    <div class="product">
                        <a href="{product['href']}" target="_blank">
                            <img src="{product['img']}" alt="{product['text']}">
                            {''.join(['<p>' + key.capitalize() + ': ' + str(value) + '</p>' for key, value in props.items()])}
                        </a>
                    </div>
                    """
                html_content += product_block
            except Exception as e:
                print(f"\u001b[31mException while generating new HTML: {e}\u001b[0m")

        html_content += self._html_template_end

        return html_content

    def generate_text_wesite_html(self, parsed_content, search_query, threshold=3, verbose=0):
        html_content = self._html_template_start

        for i, element in enumerate(parsed_content):
            request = (f"On a scale of 1 to 5, how likely is it that the menu item \"{element['text']}\" contains "
                       f"what the query '{search_query}' is searching for? Make sure the response only consists of a "
                       f"number between 1 to 5, NOTHING else")
            response = self._cheap_llm.get_response(request)
            if verbose >= 2:
                print(i, element['text'], response)
            if not '1' <= response < '6' or len(response) > 1:
                if verbose >= 1:
                    print(f"\u001b[31mWARNING! BAD RESPONSE: {response}")
                continue

            if int(response) >= threshold:
                html_content += f"""
                            <div>
                                {element['tag']}
                            </div>
                            """
        html_content += self._html_template_end
        return html_content
