from django.test import TestCase, Client
from django.urls import reverse

from ..models import Follow, Group, Post, User
from ..views import POSTS_PER_PAGE


USERNAME = 'danil'
ANOTHER_USERNAME = 'leo'
SECOND_PAGE = '?page=2'
INDEX = reverse('posts:index')
PROFILE = reverse('posts:profile', args=(USERNAME,))
FOLLOW_INDEX = reverse('posts:follow_index')


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.another_user = User.objects.create(username=ANOTHER_USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=ANOTHER_USERNAME,
            description='Тестовое описание',
        )
        cls.SECOND_PAGE_POSTS_COUNT = 1
        Post.objects.bulk_create(
            Post(
                text=f'Запись номер {index}',
                author=cls.user,
                group=cls.group
            )
            for index in range(POSTS_PER_PAGE + cls.SECOND_PAGE_POSTS_COUNT)
        )
        cls.GROUP_LIST = reverse(
            'posts:group_list', args=(cls.group.slug,)
        )
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    def test_page_content(self):
        Follow.objects.create(
            user=self.another_user,
            author=self.user
        )
        urls = {
            INDEX: POSTS_PER_PAGE,
            self.GROUP_LIST: POSTS_PER_PAGE,
            PROFILE: POSTS_PER_PAGE,
            FOLLOW_INDEX: POSTS_PER_PAGE,
            INDEX + SECOND_PAGE: self.SECOND_PAGE_POSTS_COUNT,
            self.GROUP_LIST + SECOND_PAGE: self.SECOND_PAGE_POSTS_COUNT,
            PROFILE + SECOND_PAGE: self.SECOND_PAGE_POSTS_COUNT,
            FOLLOW_INDEX + SECOND_PAGE: self.SECOND_PAGE_POSTS_COUNT,
        }
        for url, posts_count in urls.items():
            with self.subTest(url=url, page=posts_count):
                self.assertEqual(
                    len(self.another.get(url).context['page_obj']),
                    posts_count
                )
