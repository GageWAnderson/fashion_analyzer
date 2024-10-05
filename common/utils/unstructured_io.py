from unstructured.partition.html import partition_html
from unstructured.documents.elements import Element


def partition_web_page(url: str) -> list[Element]:
    """
    Partitions a web page into a list of BaseDocument objects.
    """
    return partition_html(url=url)
