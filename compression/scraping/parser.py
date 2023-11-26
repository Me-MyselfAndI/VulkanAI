import copy
from bs4 import BeautifulSoup
import math
import re
from urllib.parse import urljoin

def _sigmoid(x, multiplier):
    return 1 / (1 + math.exp(-x * multiplier))


def _find_deep_siblings(element, N, include_self=True):
    parent = element
    for i in range(N):
        parent = parent.parent
        if parent is None:
            print("Reached bedrock while finding close siblings")
            assert False

    siblings = set(parent)
    for i in range(N):
        for child in siblings:
            siblings.remove(child)
            curr_children = set(child.find_all())
            children = siblings.union(curr_children)

    if not include_self:
        siblings.remove(element)

    return siblings


def _find_common_ancestral_path(element1, element2, min_depth=0, max_depth=10):
    curr_1, curr_2 = element1, element2
    for i in range(min_depth):
        curr_1, curr_2 = curr_1.parent, curr_2.parent
        if curr_1 is None or curr_2 is None:
            return False
    for i in range(max_depth - min_depth):
        if curr_1.name != curr_2.name:
            return False
        curr_1, curr_2 = curr_1.parent, curr_2.parent
        if curr_1 is None or curr_2 is None:
            return False

    if curr_1 == curr_2:
        return curr_1

    return False


class Parser:
    def __init__(self, html=None, soup=None):
        if html is not None:
            self.soup = BeautifulSoup(html, 'html.parser')
            # self.soup = BeautifulSoup(html, 'lxml')
        elif soup is not None:
            self.soup = copy.copy(soup)
        else:
            print("\u001b[31mERROR: WRONG INITIALIZATION OF PARSER")
            assert False

    def find_container_groups(self):
        if self.soup is None:
            print("\u001b[31mERROR: PARSER UNINITIALIZED")
            assert False

        images = self.soup.find_all('img')
        products = []
        for image in images:
            curr_parent = image
            while True:
                curr_parent = curr_parent.parent
                if curr_parent.has_attr('href'):
                    products.append({'parent': curr_parent, 'img': image['src'], 'href': curr_parent['href']})
                    break
                if not curr_parent.parent:
                    # print("Reached the bedrock, seeing next image")
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
                    # print("Reached the bedrock, seeing next product")
                    break

        return products

    def find_website_menu(self, base_url, likelihood_threshold=0.5, min_common_depth=0, max_common_depth=7,
                          max_link_search_depth=5):
        if self.soup is None:
            print("\u001b[31mERROR: PARSER UNINITIALIZED")
            assert False

        def calculate_likelihood_score(element):
            likelihood_score = 0
            # TODO: Criterion 1: Check if element has similar width and height, but not both

            # Criterion 2: Check if element contains words or pictograms (less than 3 words)
            text = element.get_text()
            word_count = len(text.split())
            # TODO: implement sigmoid instead
            if word_count == 0:
                likelihood_score -= 5
            elif word_count <= 1:
                likelihood_score += 0.20
            elif word_count <= 2:
                likelihood_score += 0.20
            elif word_count <= 3:
                likelihood_score += 0.20
            elif word_count <= 4:
                likelihood_score += 0.15
            elif word_count <= 5:
                likelihood_score += 0.15
            elif word_count <= 6:
                likelihood_score += 0.15
            elif word_count <= 7:
                likelihood_score += 0.10
            elif word_count >= 10:
                likelihood_score -= 0.1 * (word_count - 10)

            # TODO: Criterion 3: Check if hovering over the element reveals another element

            # Criterion 4: Check if the element can be clicked (simplified)
            curr_element = element
            for i in range(max_link_search_depth):
                if curr_element.has_attr('href') or curr_element.has_attr('onclick'):
                    likelihood_score += 0.35
                    break
                curr_element = curr_element.parent
                if curr_element is None:
                    return likelihood_score, element

            return likelihood_score, curr_element

        menu_items = {}

        for element in self.soup.find_all():
            likelihood_score, element = calculate_likelihood_score(element)

            # Define your threshold for identifying menu items
            N = 5

            if likelihood_score >= likelihood_threshold:
                # Identify this element as a likely menu item
                # Store its Nth ancestor (you can choose N based on your design)
                nth_ancestor = element
                for _ in range(N):
                    nth_ancestor = nth_ancestor.parent

                if nth_ancestor not in menu_items:
                    menu_items[nth_ancestor] = {'items': [], 'score': None}
                if any(item['href'] == element.get('href') and item['onclick'] == element.get('onclick') for item in
                       menu_items[nth_ancestor]['items']):
                    continue
                menu_items[nth_ancestor]['items'].append(
                    {'tag': element, 'href': element.get('href'), 'onclick': element.get('onclick'),
                     'text': element.text, 'score': likelihood_score,
                     'descendant-depth': N}
                )

        for i, ancestor_i in enumerate(menu_items.copy()):
            for j, ancestor_j in enumerate(menu_items.copy()):
                if i >= j or ancestor_i not in menu_items.keys() or ancestor_j not in menu_items.keys(): continue
                elements0, elements1 = menu_items[ancestor_i]['items'], menu_items[ancestor_j]['items']
                if (set(map(lambda item: (item['href'], item['onclick']), elements0)).difference(
                        set(map(lambda item: (item['href'], item['onclick']), elements1))) == set()):
                    menu_items.pop(ancestor_j)

        non_sibling_elements = []
        for ancestor in menu_items.copy():
            elements = menu_items[ancestor]['items']
            if len(elements) <= 1:
                non_sibling_elements.append(elements[0])
                continue

        for i, el_i in enumerate(non_sibling_elements):
            for j, el_j in enumerate(non_sibling_elements[:i]):
                common_parent = _find_common_ancestral_path(el_i['tag'], el_j['tag'], min_common_depth,
                                                            max_common_depth)
                if common_parent:
                    if common_parent not in menu_items:
                        menu_items[common_parent] = {'items': [], 'score': None}
                    if el_i not in menu_items[common_parent]['items']:
                        menu_items[common_parent]['items'].append(el_i)
                    if el_j not in menu_items[common_parent]['items']:
                        menu_items[common_parent]['items'].append(el_j)

        for ancestor in menu_items.copy():
            elements = menu_items[ancestor]['items']
            if len(elements) <= 1:
                menu_items.pop(ancestor)
                continue
            for ancestor_1 in menu_items.copy():
                if ancestor_1 == ancestor:
                    continue
                elements_1 = menu_items[ancestor_1]['items']
                if set(
                        map(lambda item: (item['href'], item['onclick']), elements)
                ).difference(
                    set(
                        map(lambda item: (item['href'], item['onclick']), elements_1)
                    )
                ) == set():
                    menu_items.pop(ancestor)
                    continue

        for ancestor in menu_items.copy():
            menu_items[ancestor]['score'] = sum([item['score'] for item in elements]) / len(elements)
            for i in range(len(menu_items[ancestor]['items'])):
                href = menu_items[ancestor]['items'][i]['href']
                if href is not None and not re.match(r'^\w+:?//', href):
                    menu_items[ancestor]['items'][i]['href'] = urljoin(base_url, href)


        return menu_items

    def find_text_content(self, filter_threshold=0.15):
        # Find all <p>, <h>, <table>, <a>, <span>, IN SOME SITUATIONS <div>, <ul>, <ol>
        tag_types = {
            1.0: ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'a', 'span', 'button', 'code'],
            0.7: ['ul', 'ol']
        }

        discovered_tags = []

        for likelihood_const in tag_types.keys():
            for tag_type in tag_types[likelihood_const]:
                for tag in self.soup.find_all(tag_type):
                    text = tag.text.strip()
                    likelihood_score = likelihood_const * _sigmoid(len(text.split(' ')), multiplier=0.1) - 0.5
                    if likelihood_score < filter_threshold:
                        continue
                    discovered_tags.append(
                        {
                            'type': tag_type,
                            'tag': tag,
                            'text': tag.text,
                            'onclick': tag.onclick,
                            'likelihood_score': likelihood_score
                        }
                    )

        # Check that none of the tags is the child of another
        # discovered_tags.sort(key=lambda x: -x['likelihood_score'])
        for i in range(len(discovered_tags) - 1, -1, -1):
            for j in range(len(discovered_tags)):
                if i == j:
                    continue
                if discovered_tags[i]['text'] in discovered_tags[j]['text']:
                    discovered_tags.remove(discovered_tags[i])
                    break

        return discovered_tags


def main():
    with open('test.html', encoding='utf-8') as file:
        parser = Parser(html=file)

    print('Website Menu:\n\t', parser.find_website_menu(input("Enter the current website: ")))

    # parser.find_marketplace_product_groups()


if __name__ == "__main__":
    main()
