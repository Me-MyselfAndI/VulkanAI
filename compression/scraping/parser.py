import copy
import random

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
    text_tag_types = {
        1.0: ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'a', 'span', 'button', 'code'],
        0.7: ['ul', 'ol']
    }
    def __init__(self, url, html=None, soup=None):
        self.url = url
        if html is not None:
            self.soup = BeautifulSoup(html, 'html.parser')
            # self.soup = BeautifulSoup(html, 'lxml')
        elif soup is not None:
            self.soup = copy.copy(soup)
        else:
            print("\u001b[31mERROR: WRONG INITIALIZATION OF PARSER")
            assert False

    def find_container_groups(self, base_url, min_outer_steps_text=10, min_stop_element_count=50):
        if self.soup is None:
            print("\u001b[31mERROR: PARSER UNINITIALIZED")
            assert False

        images = self.soup.find_all('img')
        products = []
        for image in images:
            print(image)
            curr_parent = image

            while True:
                curr_parent = curr_parent.parent
                if curr_parent.has_attr('href'):
                    href = curr_parent['href']
                    if href is not None and not re.match(r'^\w+:?//', href):
                        href = urljoin(base_url, href)
                    # print(f'\t\u001b[32mReached parent with href!\u001b[0m\n\t {href}')

                    products.append({'parent': curr_parent, 'img': image.get('src', ''), 'href': href})
                    break
                if not curr_parent.parent:
                    # print("Reached the bedrock, seeing next image")
                    break

        products_to_delete = set()
        for i in range(len(products)):
            for j in range(i):
                if products[i]['parent'] == products[j]['parent'] or products[i]['parent'] in products[j]['parent'].descendants and products[i]['text'] == products[j]['text'] or products[i]['href'] == products[j]['href']:
                    products_to_delete.add(j)
                elif products[j]['parent'] in products[i]['parent'].descendants:
                    products_to_delete.add(i)

        text_tag_types = []
        for tag_types in self.text_tag_types.values():
            text_tag_types.extend(tag_types)

        for i, product in enumerate(products):
            curr_parent = product['parent']
            for _ in range(min_outer_steps_text):
                if curr_parent.parent is None or len(curr_parent.parent.find_all(text=True)) > min_stop_element_count:
                    break
                curr_parent = curr_parent.parent
            while True:
                if curr_parent is None:
                    products_to_delete.add(i)
                    break
                text_tags = curr_parent.find_all(text=True)
                if text_tags:
                    useful_text = []
                    for text_tag in text_tags:
                        text = text_tag.text
                        if text is not None and str(text).strip():
                            useful_text.append(text.strip())
                    if not useful_text:
                        curr_parent = curr_parent.parent
                        continue
                    products[i]['text'] = useful_text
                    products[i].pop('parent')
                    break
                curr_parent = curr_parent.parent

        for i in sorted(list(products_to_delete), key=lambda x: -x):
            products.pop(i)

        print("Number of products: ", len(products))
        return products

    def find_website_menu(self, likelihood_threshold=0.5, min_common_depth=0, max_common_depth=7, max_link_search_depth=5):
        if self.soup is None:
            print("\u001b[31mERROR: PARSER UNINITIALIZED")
            assert False

        def remove_same_ancestors(menu_items):
            ancestor_cleaning_dict = {}
            for i, (ancestor, elements) in enumerate(menu_items.copy().items()):
                indices = set((item['href'], item['onclick']) for item in elements['items'])

                curr_is_superset = any(key.issubset(indices) for key in ancestor_cleaning_dict)
                if curr_is_superset:
                    menu_items.pop(ancestor)
                else:
                    ancestor_cleaning_dict[frozenset(indices)] = ancestor
                for j, key in enumerate(ancestor_cleaning_dict):
                    if key == indices:
                        continue
                    if indices.issubset(key):
                        popped = menu_items.pop(ancestor_cleaning_dict.get(key, None), None)
                        if popped is None:
                            print('\u001b[33mWarning: Intersecting menu items possibly detected!\u001b[0m')

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
                    # FIXME: Temporary fix; may not work
                    if nth_ancestor.parent is None:
                        break
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

        # Remove in-page scroll references (hashtags)
        for ancestor in menu_items.copy():
            for i in range(len(menu_items[ancestor]['items']) - 1, -1, -1):
                href = menu_items[ancestor]['items'][i]['href']
                if href is None or re.match(r'^#', href):
                    menu_items[ancestor]['items'].pop(i)
            if len(menu_items[ancestor]['items']) == 0:
                menu_items.pop(ancestor)

        print()
        # Remove same items
        remove_same_ancestors(menu_items)

        # Find elements that are the only ones in their sub-menu
        # Needed to perform deep sibling join in later parts of parsing
        non_sibling_elements = []
        for ancestor in menu_items.copy():
            elements = menu_items[ancestor]['items']
            if len(elements) <= 1:
                non_sibling_elements.append(elements[0])
                continue

        # Deep sibling join
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

        # Remove same ancestors
        # It needs to be done again due to the joined deep siblings
        remove_same_ancestors(menu_items)

        # Compute score and remove properties that are irrelevant outside the method
        for ancestor in menu_items.copy():
            elements = menu_items[ancestor]['items']
            menu_items[ancestor]['score'] = sum([item['score'] for item in elements]) / len(elements)
            for i in range(len(menu_items[ancestor]['items'])):
                href = menu_items[ancestor]['items'][i]['href']
                if href is not None and not re.match(r'^\w+:?//', href):
                    menu_items[ancestor]['items'][i]['href'] = urljoin(self.url, href)
                menu_items[ancestor]['items'][i].pop('tag')
                menu_items[ancestor]['items'][i].pop('score')
                menu_items[ancestor]['items'][i].pop('descendant-depth')

        return menu_items

    def find_text_content(self, filter_threshold=0.15):
        # Find all <p>, <h>, <table>, <a>, <span>, IN SOME SITUATIONS <div>, <ul>, <ol>
        discovered_tags = []

        for likelihood_const in self.text_tag_types.keys():
            for tag_type in self.text_tag_types[likelihood_const]:
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

    print('Website Menu:\n\t', parser.find_text_content())

    # parser.find_marketplace_product_groups()


if __name__ == "__main__":
    main()
