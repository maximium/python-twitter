# encoding: utf-8
from __future__ import unicode_literals, print_function

import json
import os
import re
import sys
from tempfile import NamedTemporaryFile
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import warnings

import twitter

import responses
from responses import GET, POST
from _pytest.warning_types import PytestConfigWarning

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=PytestConfigWarning)


DEFAULT_URL = re.compile(r'https?://api\.twitter\.com/2/.*')


class ErrNull(object):
    """ Suppress output of tests while writing to stdout or stderr. This just
    takes in data and does nothing with it.
    """

    def write(self, data):
        pass


class ApiTest(unittest.TestCase):

    def setUp(self):
        self.api = twitter.Api(
            tweet_mode='extended',
            base_url_v2='https://api.twitter.com/2',
            consumer_key='test',
            consumer_secret='test',
            access_token_key='test',
            access_token_secret='test',
            sleep_on_rate_limit=False,
            chunk_size=500 * 1024)
        self._stderr = sys.stderr
        sys.stderr = ErrNull()

    def tearDown(self):
        sys.stderr = self._stderr
        pass

    @responses.activate
    def testGetSearchAdaptive(self):
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(GET, DEFAULT_URL, body=resp_data)

        resp = self.api.GetSearchAdaptive(term='twitter', return_json=False)
        self.assertEqual(len(resp), 3)
        self.assertTrue(type(resp[0]), twitter.Status)
        self.assertEqual(resp[0].id, 1521067027032588289)
        self.assertRaises(
            twitter.TwitterError,
            lambda: self.api.GetSearchAdaptive(term='test', count='test'))
        self.assertFalse(self.api.GetSearchAdaptive())

    @responses.activate
    def testGetSearchAdaptiveResultFilterUser(self):
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(GET, DEFAULT_URL, body=resp_data)

        resp = self.api.GetSearchAdaptive(term='twitter', result_filter='user')
        self.assertEqual(len(resp), 3)
        self.assertTrue(type(resp[0]), twitter.User)
        self.assertEqual(resp[0].id, 1520689095517040640)

    @responses.activate
    def testGetSearchAdaptiveExpandUser(self):
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(GET, DEFAULT_URL, body=resp_data)

        resp = self.api.GetSearchAdaptive(term='twitter', expand_user=True)
        self.assertTrue(type(resp[0].user), twitter.User)
        self.assertEqual(resp[0].user.screen_name, 'nhk_dramas')

    @responses.activate
    def testGetSearchAdaptiveQueryParameters(self):
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(
            GET,
            DEFAULT_URL,
            body=resp_data,
            match=[responses.matchers.query_param_matcher({
                'q': 'twitter min_replies:1 min_faves:2 min_retweets:3 lang:en until:2022-01-01 since:2006-06-01',
            }, strict_match=False)],
        )

        self.api.GetSearchAdaptive(
            term='twitter',
            min_replies=1,
            min_faves=2,
            min_retweets=3,
            lang='en',
            until='2022-01-01',
            since='2006-06-01'
        )

    @responses.activate
    def testGetSearchAdaptiveResultFilter(self):
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(
            GET,
            DEFAULT_URL,
            body=resp_data,
            match=[responses.matchers.query_param_matcher({'result_filter': 'image'}, strict_match=False)],
        )

        self.api.GetSearchAdaptive(
            term='twitter',
            result_filter=twitter.SearchResultFilter.IMAGE,
        )
        self.api.GetSearchAdaptive(
            term='twitter',
            result_filter='image',
        )

    @responses.activate
    def testGetSearchAdaptiveWrongResultFilter(self):
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(
            GET,
            DEFAULT_URL,
            body=resp_data,
        )

        self.assertRaises(
            twitter.TwitterError,
            lambda: self.api.GetSearchAdaptive(term='twitter', result_filter='wrongvalue')
        )

    @responses.activate
    def testGetSeachAdaptiveRawQuery(self):
        """Test raw query parameters used as it is
        without overriding or adding parameters passed as method arguments
        """
        with open('testdata/get_search_adaptive.json') as f:
            resp_data = f.read()
        responses.add(
            GET,
            DEFAULT_URL,
            match=[responses.matchers.query_param_matcher({
                'count': 100,
                'q': 'twitter',
                'result_filter': 'image',
                'tweet_mode': 'extended',  # added in Api._RequestUrl method
            })],
            body=resp_data,
        )

        self.api.GetSearchAdaptive(raw_query="q=twitter&count=100&result_filter=image", count=20)
