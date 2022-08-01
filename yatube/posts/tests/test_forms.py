import shutil
import tempfile
from xml.etree.ElementTree import Comment

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from posts.models import Group, Post, Comment

User = get_user_model()
count_new_posts: int = 1
count_new_comments: int = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание записей в БД для тестов forms"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post_1 = Post.objects.create(
            id=0,
            author=cls.user,
            text='Тестовый пост 1',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание неавторизованного и авторизованного клиентов."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_post_create_for_authorized(self):
        """
        Валидная форма создает запись в Post и верно перенаправляет
        авторизованного пользователя.
        """
        posts_count = Post.objects.count()
        small_1_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_1.gif',
            content=small_1_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args={self.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + count_new_posts)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 2',
                group=self.group.id,
                image='posts/small_1.gif'
            ).exists()
        )

    def test_post_create_for_anonymous(self):
        """
        Валидная форма не создает запись в Post и верно перенаправляет
        не авторизованного пользователя.
        """
        posts_count = Post.objects.count()
        small_2_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_2.gif',
            content=small_2_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/create/'))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_for_authorized(self):
        """
        Валидная форма редактирует запись в Post и верно перенаправляет
        авторизованного пользователя.
        """
        posts_count = Post.objects.count()
        small_3_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_3.gif',
            content=small_3_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 100500',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={PostFormTest.post_1.id}),
            data=form_data,
            follow=True
        )
        reverse_post_detail = reverse(
            'posts:post_detail', args={PostFormTest.post_1.id}
        )
        response_2 = self.authorized_client.get(reverse_post_detail)
        post_text_1 = response_2.context.get('posts').text
        post_image_1 = response_2.context.get('posts').image
        context_post = {
            post_text_1: 'Тестовый текст 100500',
            post_image_1: 'posts/small_3.gif'
        }
        self.assertRedirects(response, reverse_post_detail)
        self.assertEqual(Post.objects.count(), posts_count)
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_post_edit_for_anonymous(self):
        """
        Валидная форма не редактирует запись в Post и верно перенаправляет
        не авторизованного пользователя.
        """
        posts_count = Post.objects.count()
        small_4_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_4.gif',
            content=small_4_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 100500',
            'image': uploaded,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', args={PostFormTest.post_1.id}),
            data=form_data,
            follow=True
        )
        response_2 = self.guest_client.get(reverse(
            'posts:post_detail', args={PostFormTest.post_1.id}
        ))
        post_text_1 = response_2.context.get('posts').text
        post_image_1 = response_2.context.get('posts').image
        context_post = {
            post_text_1: 'Тестовый пост 1',
            post_image_1: ''
        }
        self.assertRedirects(response, '/auth/login/?next=/posts/0/edit/')
        self.assertEqual(Post.objects.count(), posts_count)
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание записей в БД для тестов forms"""
        super().setUpClass()
        cls.user_2 = User.objects.create_user(username='user')
        cls.post_3 = Post.objects.create(
            id=2,
            author=cls.user_2,
            text='Тестовый пост 3'
        )

    def setUp(self):
        """Создание неавторизованного и авторизованного клиентов."""
        self.anonymous_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(CommentFormTest.user_2)

    def test_add_comment_for_authorized(self):
        """
        Валидная форма создает комментарий и верно перенаправляет
        авторизованного пользователя.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment', args={CommentFormTest.post_3.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args={CommentFormTest.post_3.id}
        ))
        self.assertEqual(
            Comment.objects.count(), comments_count + count_new_comments
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
            ).exists()
        )

    def test_add_comment_for_anonymous(self):
        """
        Валидная форма не создает комментарий и верно перенаправляет
        не авторизованного пользователя.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий 2'
        }
        response = self.anonymous_client.post(
            reverse('posts:add_comment', args={CommentFormTest.post_3.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/2/comment/'))
        self.assertEqual(
            Comment.objects.count(), comments_count
        )
