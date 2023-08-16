import copy

from bs4 import BeautifulSoup


class Parser:
    def __init__(self, html=None, soup=None):
        if html is not None:
            self.html = BeautifulSoup(html, 'html.parser')
        elif soup is not None:
            self.html = copy.copy(soup)
        else:
            print("\u001b[31mERROR: WRONG INITIALIZATION OF PARSER")

    def find_product_groups(self):
        images = self.html.find_all("img")

        products = []
        for image in images:
            curr_parent = image
            while True:
                curr_parent = curr_parent.parent
                if curr_parent.has_attr('href'):
                    products.append({'parent': curr_parent, 'img': image['src'], 'href': curr_parent['href']})
                    break
                if not curr_parent.parent:
                    print("Reached the bedrock, seeing next image")
                    break

        for i, product in enumerate(products):
            curr_parent = product['parent']
            while True:
                curr_parent = curr_parent.parent
                text = curr_parent.find_all(text=True)
                if text:
                    products[i]['text'] = text
                    products[i].pop('parent')
                    break
                if not curr_parent.parent:
                    print("Reached the bedrock, seeing next product")
                    break

        # for product in products:
        #     print(product['text'], product['img'], product['href'], sep='\n\t', end='\n')

        return products


def main():
    with open('test.html', encoding='utf-8') as file:
        parser = Parser(html=file)

    parser.find_product_groups()


if __name__ == "__main__":
    main()
