# -*- coding: utf-8 -*-

"""pybooru.api_danbooru

This module contains all API calls of Gelbooru.

Classes:
    GelbooruApi_Mixin -- Contains all API endspoints.
"""

# __future__ imports
from __future__ import absolute_import

# pybooru imports
from .exceptions import PybooruAPIError


class GelbooruApi_Mixin(object):
    """Contains all Gelbooru API calls.
    * API Version commit: ?
    * Doc: https://gelbooru.me/index.php?page=wiki&s=view&id=18780
    """

    def post_list(self, **params):
        """Get a list of posts.

        Parameters:
            page (int): The page number.
            tags (str): The tags to search for. Any tag combination that works
                        on the web site will work here. This includes all the
                        meta-tags.
        """
        params['pid'] = params.pop('page')
        return self._get('post', params)


    def tag_list(self, name_pattern=None, name=None, order=None, orderby=None):
        """Get a list of tags.

        Parameters:
            name_pattern (str): Can be: part or full name.
            name (str): Allows searching for tag with given name
            order (str): Can be: ASC, DESC.
            orderby (str): Can be: name, date, count.
        """
        params = {
            'name_pattern': name_pattern,
            'name': name,
            'order': order,
            'orderby': orderby
            }
        return self._get('tag', params)
