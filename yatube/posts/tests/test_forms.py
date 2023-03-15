import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Comment, Group, Post, User


USERNAME = 'danil'
ANOTHER_USERNAME = 'leo'
GROUP_SLUG = 'test-slug'
GROUP_SLUG_NEW = 'test-slug_new'
UPLOAD_TO = Post._meta.get_field("image").upload_to
CREATE_POST = reverse('posts:post_create')
PROFILE = reverse(
    'posts:profile',
    args=(USERNAME,)
)
GROUP_LIST = reverse(
    'posts:group_list', args=(GROUP_SLUG,)
)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            slug='test-slug-new',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=SimpleUploadedFile(
                name='small_default.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.EDIT_POST = reverse('posts:post_edit', args={cls.post.id})
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            args=(cls.post.id,)
        )
        cls.EDIT_LOGIN = f'{reverse("users:login")}?next={cls.EDIT_POST}'
        cls.ADD_COMMENT = reverse(
            'posts:add_comment',
            args=(cls.post.id,)
        )
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts = set(Post.objects.all())
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized.post(
            CREATE_POST,
            data=form_data,
            follow=True
        )
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertRedirects(response, PROFILE)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(
            post.image,
            f'{UPLOAD_TO}{form_data["image"].name}'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_guest(self):
        """Аноним не может создавать посты"""
        posts = set(Post.objects.all())
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        self.guest.post(
            CREATE_POST,
            data=form_data,
            follow=True
        )
        self.assertEqual(posts, set(Post.objects.all()))

    def test_post_edit(self):
        another_uploaded_file = SimpleUploadedFile(
            name='another_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Изменяем текст',
            'group': self.group_new.id,
            'image': another_uploaded_file,
        }
        response = self.authorized.post(
            self.EDIT_POST,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL)
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image,
            f'{UPLOAD_TO}{form_data["image"].name}'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_author(self):
        """Валидная форма не изменит запись в Post если неавторизован."""
        new_uploaded_file = SimpleUploadedFile(
            name='new_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Изменяем текст',
            'group': self.group_new.id,
            'image': new_uploaded_file
        }
        clients = {
            self.guest: self.EDIT_LOGIN,
            self.another: self.POST_DETAIL
        }
        for client, redirect in clients.items():
            with self.subTest(client=client):
                response = client.post(
                    self.EDIT_POST,
                    data=form_data,
                    follow=True,
                )
                self.assertRedirects(response, redirect)
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_edit_show_correct_context(self):
        """Шаблоны create и create_edit
        сформированы с правильным контекстом."""
        urls = (
            self.EDIT_POST,
            CREATE_POST
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for url in urls:
            response = self.authorized.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_add_comment_guest(self):
        """Комментировать посты может только авторизованный пользователь"""
        comments_before = set(Comment.objects.all())
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.guest.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True
        )
        comments_after = set(Comment.objects.all())
        self.assertEqual(comments_before, comments_after)

    def test_add_comment(self):
        comments_before = set(Comment.objects.all())
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.authorized.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True
        )
        comments_after = set(Comment.objects.all())
        difference = comments_after.difference(comments_before)
        self.assertEqual(len(difference), 1)
        comment = difference.pop()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
