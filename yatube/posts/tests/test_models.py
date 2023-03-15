from django.test import TestCase

from ..models import (
    Comment, Follow, Group, Post, User,
    COMMENT_STR_SIZE, POST_STR_SIZE, GROUP_STR_SIZE,
    FOLLOW_STR
)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='danil')
        cls.another_user = User.objects.create(username='leo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.another_user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        object_names = (
            (self.post, self.post.text[:POST_STR_SIZE]),
            (self.group, self.group.title[:GROUP_STR_SIZE]),
            (self.comment, self.comment.text[:COMMENT_STR_SIZE]),
            (
                self.follow,
                FOLLOW_STR.format(
                    user=self.follow.user.username,
                    author=self.follow.author.username
                )
            )
        )
        for object_name, expected_object_name in object_names:
            with self.subTest(expected_object_names=expected_object_name):
                self.assertEqual(expected_object_name, str(object_name))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        verbose_name = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in verbose_name.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).verbose_name, expected
                )
