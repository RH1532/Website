from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


OK = HTTPStatus.OK
NOT_FOUND = HTTPStatus.NOT_FOUND
REDIRECT = HTTPStatus.FOUND
USERNAME = 'danil'
ANOTHER_USERNAME = 'leo'
GROUP_SLUG = 'test-slug'
LOGIN_INTRO = reverse('users:login') + '?next='
UNEXISTING_PAGE = '/unexisting_page/'
INDEX = reverse('posts:index')
PROFILE = reverse('posts:profile', args=(USERNAME,))
PROFILE_NEW = reverse('posts:profile', args=(ANOTHER_USERNAME,))
CREATE_POST = reverse('posts:post_create')
CREATE_REDIRECT = (LOGIN_INTRO + CREATE_POST)
GROUP_LIST = reverse(
    'posts:group_list', args=(GROUP_SLUG,)
)
FOLLOW = reverse(
    'posts:profile_follow',
    args=(ANOTHER_USERNAME,)
)
FOLLOW_REDIRECT = (LOGIN_INTRO + FOLLOW)
UNFOLLOW = reverse(
    'posts:profile_unfollow',
    args=(ANOTHER_USERNAME,)
)
UNFOLLOW_REDIRECT = (LOGIN_INTRO + UNFOLLOW)
FOLLOW_INDEX = reverse('posts:follow_index')
FOLLOW_INDEX_REDIRECT = (LOGIN_INTRO + FOLLOW_INDEX)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.another_user = User.objects.create(username=ANOTHER_USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            args=(cls.post.id,)
        )
        cls.EDIT_POST = reverse(
            'posts:post_edit',
            args=(cls.post.id,)
        )
        cls.EDIT_REDIRECT = (
            LOGIN_INTRO
            + reverse('posts:post_edit', args={cls.post.id})
        )
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    def test_http_status(self):
        """Тест кодов возврата"""
        cases = [
            [self.authorized, self.EDIT_POST, OK],
            [self.authorized, CREATE_POST, OK],
            [self.authorized, FOLLOW, REDIRECT],
            [self.authorized, UNFOLLOW, REDIRECT],
            [self.authorized, FOLLOW_INDEX, OK],
            [self.guest, INDEX, OK],
            [self.guest, GROUP_LIST, OK],
            [self.guest, PROFILE, OK],
            [self.guest, self.POST_DETAIL, OK],
            [self.guest, self.EDIT_POST, REDIRECT],
            [self.guest, CREATE_POST, REDIRECT],
            [self.guest, UNEXISTING_PAGE, NOT_FOUND],
            [self.guest, FOLLOW, REDIRECT],
            [self.guest, UNFOLLOW, REDIRECT],
            [self.guest, FOLLOW_INDEX, REDIRECT],
            [self.another, self.EDIT_POST, REDIRECT],
            [self.another, FOLLOW, REDIRECT],
            [self.another, UNFOLLOW, NOT_FOUND],
            [self.another, FOLLOW_INDEX, OK],
        ]
        for client, url, status in cases:
            with self.subTest(
                client=client, url=url, status=status,
            ):
                self.assertEqual(client.get(url).status_code, status)

    def test_redirect_anonymous_on_auth_login(self):
        """Страницы перенаправляют анонимного и непрвильного
        пользователя на страницу логина."""
        cases = [
            [self.authorized, FOLLOW, PROFILE_NEW],
            [self.authorized, UNFOLLOW, PROFILE_NEW],
            [self.guest, self.EDIT_POST, self.EDIT_REDIRECT],
            [self.guest, CREATE_POST, CREATE_REDIRECT],
            [self.guest, FOLLOW, FOLLOW_REDIRECT],
            [self.guest, FOLLOW_INDEX, FOLLOW_INDEX_REDIRECT],
            [self.guest, UNFOLLOW, UNFOLLOW_REDIRECT],
            [self.another, self.EDIT_POST, self.POST_DETAIL],
            [self.another, FOLLOW, PROFILE_NEW],
        ]
        for client, address, template in cases:
            with self.subTest(
                client=client, address=address, template=template
            ):
                self.assertRedirects(
                    client.get(address, follow=True),
                    template
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX: 'posts/index.html',
            GROUP_LIST: 'posts/group_list.html',
            PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.EDIT_POST: 'posts/create_post.html',
            CREATE_POST: 'posts/create_post.html',
            UNEXISTING_PAGE: 'core/404.html',
            FOLLOW_INDEX: 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.authorized.get(address),
                    template
                )
