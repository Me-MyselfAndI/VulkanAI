import openai
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urljoin, urlparse

from compression.ai.astica_engine import AsticaEngine
from compression.ai.gpt_engine import GPTEngine


def scrape_website(url):
    driver = webdriver.Chrome()  # or webdriver.Chrome(), depending on your installed browser
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup


def get_important_content(website_content, important_tags=('a', 'li', 'p', 'div')):
    soup = BeautifulSoup(website_content, 'html.parser')
    important_content = [tag.get_text(strip=True) for tag in soup.find_all(important_tags)]
    image_tags = soup.find_all('img')
    image_sources = [tag.get('src') for tag in image_tags if tag.get('src')]
    combined_content = important_content + image_sources

    return combined_content


def generate_website(product_info):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Amazon Products</title>
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

    for product in product_info:
        image_url = product.get('image', '')  # If 'image' key is missing, it defaults to an empty string.
        product_block = f"""
        <div class="product">
            <a href="{product.get('link', '#')}" target="_blank">
                <img src="{image_url}" alt="{product.get('title', 'Amazon Product')}">
                <p>{product.get('title', 'Amazon Product')}</p>
            </a>
        </div>
        """
        html_content += product_block

    html_content += """
        </div>
    </body>
    </html>
    """

    with open("test_input.html", "w") as file:
        file.write(html_content)

    print("Website generated: test_input.html")


def get_product_info(soup, base_url):
    product_info = []
    for product in soup.find_all('div', {'class': 'sg-col-inner'}):
        info = {}
        try:
            title = product.text
        except Exception:
            title = product.find('span').text  # , {'class': 'a-size-medium'})
        link = product.find('a', {'class': 'a-link-normal'})
        image = product.find('img', {'class': 's-image'})
        if title:
            info['title'] = title
        if link and link.get('href'):
            info['link'] = urljoin(base_url, link.get('href'))
        if image and image.get('src'):
            info['image'] = image.get('src')
        if info:
            product_info.append(info)
    return product_info


def get_ai_assessment(product, user_input, astica):
    try:
        astica_result = astica.get_image_description(product['image'])

        prompt = f"Given the user's preference of '{user_input}', does the product titled '{product['title']}' and described as '{astica_result}' match the " \
                 f"criteria? Answer yes or no only "
        gpt_result = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])

        assessment = gpt_result.choices[0].message.content.strip().lower()
        print(product, assessment, "\n")
        return assessment == "yes"
    except Exception:
        return "no"


def filter_products(product_info, user_input):
    filtered_products = []
    for product in product_info:
        if get_ai_assessment(product, user_input):
            filtered_products.append(product)
    return filtered_products


def main():
    url = 'https://www.amazon.com/s?k=white+watch&crid=GVER7X5ZPBD&sprefix=white+watch%2Caps%2C234&ref=nb_sb_noss_1'
    soup = scrape_website(url)
    product_info = get_product_info(soup)
    for product in product_info:
        print(product)

    # Get user input
    user_input = input("Please specify your product preferences: ")

    filtered_product_info = filter_products(product_info, user_input)

    generate_website(filtered_product_info)


if __name__ == "__main__":
    main()
