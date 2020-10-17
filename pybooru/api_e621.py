# -*- coding: utf-8 -*-

"""pybooru.api_danbooru

This module contains all API calls of E621.

Classes:
    E621Api_Mixin -- Contains all API endspoints.
"""

# __future__ imports
from __future__ import absolute_import

# pybooru imports
from .exceptions import PybooruAPIError


class E621Api_Mixin(object):
    """Contains all E621 API calls.
    * API Version commit: ?
    * Doc: https://e621.net/help/api#posts
    """

    def post_list(self, **params):
        """Get a list of posts.

        Parameters:
            page (int): The page number.
            tags (str): The tags to search for. Any tag combination that works
                        on the web site will work here. This includes all the
                        meta-tags.
        """

        return self._get('posts.json', params)


    def tag_list(self, name=None, category=None, order=None, hide_empty=None, has_wiki=None, has_artist=None, extra_params={}):
        """Get a list of tags.

        Parameters:
            name_matches (str): A tag name expression to match against
            category (int): Filters results to a particular category
            order (str): date/count/name
            has_wiki (str): Show only tags with wiki, true/false
            has_artist (str): true/false

        """
        params = {
            'search[name_matches]': name,
            'search[category]': category,
            'search[order]': order,
            'search[hide_empty]': hide_empty,
            'search[has_wiki]': has_wiki,
            'search[has_artist]': has_artist,
            }
        params.update(extra_params)
        return self._get('tags.json', params)
