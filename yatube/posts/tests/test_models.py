from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, Comment, Follow

User = get_user_model()
quantity_letters: int = 15


class PostModelTest(TestCase):
    """Создание записей в БД для тестов models"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_1 = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост на проверку пятнадцати символов',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий на проверку пятнадцати символов'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_1
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        models_str = {
            group: group.title,
            post: post.text[:quantity_letters],
            comment: comment.text[:quantity_letters],
            follow: follow.user.username
        }
        for model, expected_value in models_str.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_value)
