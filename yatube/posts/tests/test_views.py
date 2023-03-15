from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User


USERNAME = 'danil'
ANOTHER_USERNAME = 'leo'
GROUP_SLUG = 'test-slug'
GROUP_SLUG_NEW = 'test-slug_new'
INDEX = reverse('posts:index')
PROFILE = reverse('posts:profile', args=(USERNAME,))
GROUP_LIST = reverse(
    'posts:group_list', args=(GROUP_SLUG,)
)
GROUP_NEW = reverse(
    'posts:group_list', args=(GROUP_SLUG_NEW,)
)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
FOLLOW = reverse(
    'posts:profile_follow',
    args=(ANOTHER_USERNAME,)
)
UNFOLLOW = reverse(
    'posts:profile_unfollow',
    args=(ANOTHER_USERNAME,)
)
FOLLOW_INDEX = reverse('posts:follow_index')


class PostPagesTests(TestCase):
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
        cls.group_new = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG_NEW,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=SimpleUploadedFile(
                name='small_default.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    def test_show_correct_context(self):
        """Шаблон равен ожидемому контексту"""
        Follow.objects.create(
            user=self.another_user,
            author=self.user
        )
        urls = {
            INDEX: 'page_obj',
            GROUP_LIST: 'page_obj',
            PROFILE: 'page_obj',
            self.POST_DETAIL: 'post',
            FOLLOW_INDEX: 'page_obj'
        }
        for url, context in urls.items():
            with self.subTest(url=url):
                data = self.another.get(url)
                if url != self.POST_DETAIL:
                    self.assertEqual(len(data.context[context]), 1)
                    post = data.context[context][0]
                else:
                    post = data.context[context]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_group_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized.get(
            GROUP_LIST
        )
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.description, self.group.description)

    def test_author_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.assertEqual(
            self.authorized.get(PROFILE).context['author'],
            self.user
        )

    def test_post_not_in_mistake_page(self):
        urls = (
            GROUP_NEW,
            FOLLOW_INDEX,
        )
        for url in urls:
            self.assertNotIn(
                self.post,
                self.authorized.get(url).context['page_obj']
            )

    def test_cache_index_pages(self):
        """Проверяем работу кэша главной страницы."""
        first_response = self.client.get(INDEX)
        Post.objects.all().delete()
        self.assertEqual(
            first_response.content,
            self.client.get(INDEX).content
        )
        cache.clear()
        self.assertNotEqual(
            first_response.content,
            self.client.get(INDEX).content
        )

    def test_authorized_follow(self):
        """Авторизованный пользователь может
        подписываться на других пользователей"""
        self.authorized.get(FOLLOW)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user
            ).exists()
        )

    def test_authorized_unfollow(self):
        """Авторизованный пользователь может
        отписываться от других пользователей"""
        Follow.objects.create(
            user=self.user,
            author=self.another_user
        )
        self.authorized.get(UNFOLLOW)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user
            ).exists()
        )
