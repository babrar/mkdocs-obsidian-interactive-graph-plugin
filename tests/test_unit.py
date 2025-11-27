# Standard Libraries
from unittest.mock import MagicMock, Mock
from typing import Callable

# Third party libraries
import pytest

# Local application/library specific imports
from obsidian_interactive_graph.plugin import ObsidianInteractiveGraphPlugin

# Type alias for the factory fixture
PageFactory = Callable[..., MagicMock]


@pytest.fixture
def plugin() -> ObsidianInteractiveGraphPlugin:
    """Initialize the plugin with a mock configuration."""
    plugin_instance = ObsidianInteractiveGraphPlugin()
    config = MagicMock()
    config.site_name = "TestSite"
    plugin_instance.on_config(config)
    return plugin_instance


@pytest.fixture
def mock_page_factory() -> PageFactory:
    """
    Provide a factory to create mock MkDocs Page objects.

    Returns:
        A callable that accepts (title, src_uri, abs_url, content, is_index)
        and returns a configured MagicMock.
    """
    def _create(
        title: str,
        src_uri: str,
        abs_url: str,
        content: str,
        is_index: bool = False
    ) -> MagicMock:
        page = MagicMock()
        page.title = title
        page.file.src_uri = src_uri
        page.abs_url = abs_url
        page.markdown = content
        page.is_index = is_index
        # Mock read_source to prevent disk I/O during unit tests
        page.read_source = Mock()
        return page

    return _create


def test_collect_pages(
    plugin: ObsidianInteractiveGraphPlugin, mock_page_factory: PageFactory
) -> None:
    """
    Verify that the plugin correctly registers pages into the internal node dictionary.

    The plugin uses the site name and source URI to generate unique keys for the
    nodes map, which is later used for link resolution.
    """
    nav = MagicMock()
    page1 = mock_page_factory(
        "Home", "index.md", "/index.html", "Hello", is_index=True
    )
    page2 = mock_page_factory("About", "about.md", "/about/", "World")
    nav.pages = [page1, page2]

    plugin.collect_pages(nav, MagicMock())

    assert "TestSite/index" in plugin.nodes
    assert "TestSite/about" in plugin.nodes


def test_wikilink_parsing(
    plugin: ObsidianInteractiveGraphPlugin, mock_page_factory: PageFactory
) -> None:
    """
    Verify that regex parsing correctly identifies wikilinks and resolves them to node IDs.

    This test pre-populates the node dictionary to simulate a state where
    navigation has already been processed, ensuring the parser can find
    the target ID for '[[target]]'.
    """
    plugin.nodes = {
        "TestSite/source": {"id": 1, "symbolSize": 1, "is_index": False},
        "TestSite/target": {"id": 2, "symbolSize": 1, "is_index": False},
    }

    md_content = "Link to [[target]]"
    source_page = mock_page_factory("Source", "source.md", "/source/", md_content)

    plugin.parse_markdown(md_content, source_page)

    links = plugin.data["links"]

    assert len(links) == 1
    assert links[0]["source"] == "1"
    assert links[0]["target"] == "2"
