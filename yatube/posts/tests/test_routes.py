from django.test import TestCase
from django.urls import reverse

from ..urls import app_name


POST_ID = 1
TEST_SLUG = 'test-slug'
USERNAME = 'HasNoName'
ROUTES_NAMES = [
    ['index', None, '/'],
    ['group_list', (TEST_SLUG,), f'/group/{TEST_SLUG}/'],
    ['profile', (USERNAME,), f'/profile/{USERNAME}/'],
    ['post_detail', (POST_ID,), f'/posts/{POST_ID}/'],
    ['post_edit', (POST_ID,), f'/posts/{POST_ID}/edit/'],
    ['post_create', None, '/create/'],
    ['add_comment', (POST_ID,), f'/posts/{POST_ID}/comment/'],
    ['profile_follow', (USERNAME,), f'/profile/{USERNAME}/follow/'],
    ['profile_unfollow', (USERNAME,), f'/profile/{USERNAME}/unfollow/'],
    ['follow_index', None, '/follow/']
]


class RoutesTest(TestCase):
    def test_calculations_give_the_expected_explicit_urls(self):
        """Расчеты дают ожидаемые в ТЗ явные урлы"""
        for route, args, url in ROUTES_NAMES:
            self.assertEqual(
                reverse(
                    f'{app_name}:{route}',
                    args=args
                ),
                url
            )
