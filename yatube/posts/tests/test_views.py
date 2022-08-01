import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from posts.models import Post, Group, Comment, Follow


User = get_user_model()
posts_on_first_page: int = 10
posts_on_second_page: int = 3
count_posts: int = 13
posts_on_another_group: int = 0
posts_on_another_author: int = 0
count_new_follows: int = 1
id_post: int = 0
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
uploaded = SimpleUploadedFile(
    name='small.gif',
    content=small_gif,
    content_type='image/gif'
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание записей в БД для тестов views"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='rain')
        cls.user_3 = User.objects.create_user(username='snow')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post_1 = Post.objects.create(
            id=0,
            author=cls.user,
            text='Тестовый пост 1',
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post_1,
            author=cls.user,
            text='Тестовый комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание авторизованного и не авторизованного клиентов."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_not_author = Client()
        self.client_not_follow = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        self.client_not_author.force_login(PostViewsTest.user_2)
        self.client_not_follow.force_login(PostViewsTest.user_3)
        cache.clear()

    def test_pages_uses_correct_template_for_anonymous(self):
        """
        URL-адрес использует соответствующий шаблон для
        не авторизованного пользователя.
        """
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', args={PostViewsTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args={PostViewsTest.post_1.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args={PostViewsTest.post_1.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', args={PostViewsTest.post_1.id}
            ): 'users/login.html',
            reverse('posts:post_create'): 'users/login.html',
            reverse(
                'posts:add_comment', args={PostViewsTest.post_1.id}
            ): 'users/login.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name, follow=True)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_authorized(self):
        """
        URL-адрес использует соответствующий шаблон для
        авторизованного пользователя.
        """
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', args={PostViewsTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args={PostViewsTest.post_1.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args={PostViewsTest.post_1.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', args={PostViewsTest.post_1.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:add_comment', args={PostViewsTest.post_1.id}
            ): 'posts/post_detail.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(
                    reverse_name, follow=True
                )
                self.assertTemplateUsed(response, template)

    def test_page_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][id_post]
        post_text_0 = first_object.text
        post_image_0 = first_object.image
        context_post = {
            post_text_0: 'Тестовый пост 1',
            post_image_0: 'posts/small.gif'
        }
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_page_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={PostViewsTest.group.slug})
        )
        first_object = response.context['page_obj'][id_post]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image
        context_post = {
            post_text_0: 'Тестовый пост 1',
            post_group_0: 'Тестовая группа',
            post_image_0: 'posts/small.gif'
        }
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_page_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', args={PostViewsTest.post_1.author.username}
        ))
        first_object = response.context['page_obj'][id_post]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_image_0 = first_object.image
        context_post = {
            post_text_0: 'Тестовый пост 1',
            post_author_0: 'auth',
            post_image_0: 'posts/small.gif'
        }
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_page_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args={PostViewsTest.post_1.id})
        )
        first_object = response.context.get('posts')
        post_text_0 = first_object.text
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        comments = response.context.get('comments')
        for comment in comments:
            comment.text
        post_comment_0 = comment.text
        context_post = {
            post_text_0: 'Тестовый пост 1',
            post_image_0: 'posts/small.gif',
            post_id_0: 0,
            post_comment_0: 'Тестовый комментарий'
        }
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)
        text_form = response.context.get('form').fields.get('text')
        self.assertIsInstance(text_form, forms.fields.CharField)

    def test_page_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args={PostViewsTest.post_1.id})
        )
        post_id_0 = response.context.get('post').id
        self.assertEqual(post_id_0, id_post)
        post_is_edit_0 = response.context.get('is_edit')
        self.assertTrue(post_is_edit_0)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_page_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_page_index_show_correct_post_with_group(self):
        """Пост с указанной группой показан на странице index."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][id_post]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_author_0 = first_object.author.username
        context_post_with_group = {
            post_text_0: 'Тестовый пост 1',
            post_group_0: 'Тестовая группа',
            post_author_0: 'auth'
        }
        for field, expected in context_post_with_group.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_page_group_list_show_correct_post_with_group(self):
        """Пост с указанной группой показан на странице group_list."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={PostViewsTest.group.slug})
        )
        first_object = response.context['page_obj'][id_post]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_author_0 = first_object.author.username
        context_post_with_group = {
            post_text_0: 'Тестовый пост 1',
            post_group_0: 'Тестовая группа',
            post_author_0: 'auth'
        }
        for field, expected in context_post_with_group.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_page_profile_show_correct_post_with_group(self):
        """Пост с указанной группой показан на странице profile."""
        response = self.authorized_client.get(reverse(
            'posts:profile', args={PostViewsTest.post_1.author.username}
        ))
        first_object = response.context['page_obj'][id_post]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_author_0 = first_object.author.username
        context_post_with_group = {
            post_text_0: 'Тестовый пост 1',
            post_group_0: 'Тестовая группа',
            post_author_0: 'auth'
        }
        for field, expected in context_post_with_group.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_page_another_group_list_show_correct_post_with_group(self):
        """Пост с указанной группой не показан на странице другой группы."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={PostViewsTest.group_2.slug})
        )
        self.assertEqual(
            len(response.context['page_obj']), posts_on_another_group
        )

    def test_page_post_detail_show_correct_comment(self):
        """Комментарий отображается на странице поста."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args={PostViewsTest.post_1.id})
        )
        first_object = response.context.get('posts')
        post_text_0 = first_object.text
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        comments = response.context.get('comments')
        for comment in comments:
            comment.text
        post_comment_0 = comment.text
        context_post = {
            post_text_0: 'Тестовый пост 1',
            post_image_0: 'posts/small.gif',
            post_id_0: 0,
            post_comment_0: 'Тестовый комментарий'
        }
        for field, expected in context_post.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_follow_for_authorized(self):
        """
        Авторизованный пользователь может подписываться и отписываться на
        автора.
        """
        follow_count = Follow.objects.count()
        self.client_not_author.get(
            reverse(
                'posts:profile_follow', args={PostViewsTest.user.username}
            )
        )
        self.assertEqual(
            Follow.objects.count(), follow_count + count_new_follows
        )
        self.client_not_author.get(
            reverse(
                'posts:profile_unfollow', args={PostViewsTest.user.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_for_anonymous(self):
        """Неавторизованный пользователь не может подписываться автора."""
        follow_count = Follow.objects.count()
        self.guest_client.get(
            reverse(
                'posts:profile_follow', args={PostViewsTest.user.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_for_authorized(self):
        """Автор не может подписываться сам на себя"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow', args={PostViewsTest.user.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_page_follow_index_for_follower(self):
        """
        Посты автора на которого вы подписаны отображаются на follow_index.
        """
        Follow.objects.create(
            user=PostViewsTest.user, author=PostViewsTest.user_2
        )
        post = Post.objects.create(
            text='Тестируем',
            author=PostViewsTest.user_2,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts_new = response.context['page_obj']
        self.assertIn(post, posts_new)

    def test_page_follow_index_for_not_follower(self):
        """
        Посты автора на которого вы не подписаны не отображаются на
        follow_index.
        """
        post = Post.objects.create(
            text='Тестируем',
            author=PostViewsTest.user_2,
        )
        response = self.client_not_follow.get(reverse('posts:follow_index'))
        posts_new = response.context['page_obj']
        self.assertNotIn(post, posts_new)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание записей в БД для тестов paginator"""
        super().setUpClass()
        cls.new_user = User.objects.create(username='user')
        cls.user_4 = User.objects.create(username='user_4')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание второй группы'
        )
        cls.posts = []
        for i in range(count_posts):
            cls.posts.append(Post(
                id=i,
                text=f'Тестовый пост № {i}',
                author=cls.new_user,
                group=cls.group_1,
                image=uploaded
            ))
        Post.objects.bulk_create(cls.posts)
        cls.follow = Follow.objects.create(
            user=cls.user_4,
            author=cls.new_user
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.new_user)
        cls.authorized_client_follow = Client()
        cls.authorized_client_follow.force_login(cls.user_4)

    def setUp(self):
        """Чистим кэш."""
        cache.clear()

    def test_first_page_index_contains_ten_records(self):
        """Проверка: кол-во постов на первой странице index равно 10."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), posts_on_first_page
        )

    def test_second_page_index_contains_three_records(self):
        """Проверка: кол-во постов на второй странице index равно 3."""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page
        )

    def test_first_page_group_list_contains_ten_records(self):
        """Проверка: кол-во постов на первой странице group_list равно 10."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', args={PaginatorViewsTest.group_1.slug}
        ))
        self.assertEqual(
            len(response.context['page_obj']), posts_on_first_page
        )

    def test_second_page_group_list_contains_three_records(self):
        """Проверка: кол-во постов на второй странице group_list равно 3."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', args={PaginatorViewsTest.group_1.slug}
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page
        )

    def test_first_page_profile_contains_ten_records(self):
        """Проверка: кол-во постов на первой странице profile равно 10."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'user'}
        ))
        self.assertEqual(
            len(response.context['page_obj']), posts_on_first_page
        )

    def test_second_page_profile_contains_three_records(self):
        """Проверка: кол-во постов на второй странице profile равно 3."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'user'}
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page
        )

    def test_first_page_follow_index_contains_ten_records(self):
        """Проверка: кол-во постов на первой странице profile равно 10."""
        response = self.authorized_client_follow.get(reverse(
            'posts:follow_index'
        ))
        self.assertEqual(
            len(response.context['page_obj']), posts_on_first_page
        )

    def test_second_page_follow_index_contains_three_records(self):
        """Проверка: кол-во постов на второй странице profile равно 3."""
        response = self.authorized_client_follow.get(reverse(
            'posts:follow_index'
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page
        )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание записей в БД для тестов cache."""
        super().setUpClass()
        cls.user_new = User.objects.create_user(username='auth')
        cls.user_cache = User.objects.create_user(username='cachemen')
        cls.group_cache = Group.objects.create(
            title='Группа для теста кэша',
            slug='test-slug-cache',
            description='Тестовое описание',
        )

    def setUp(self):
        """Создание авторизованного и не авторизованного клиентов."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheViewsTest.user_new)
        cache.clear()

    def test_index_page_caches_content_for_authorized(self):
        """
        Страница index отдает кэшированный контент для
        авторизованного пользователя.
        """
        post = Post.objects.create(
            text='Тестируем кеш для авторизованного пользователя',
            author=CacheViewsTest.user_cache,
            group=CacheViewsTest.group_cache
        )
        response = self.authorized_client.get(reverse('posts:index'))
        content_old = response.content
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, content_old)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, content_old)

    def test_index_page_caches_content_for_anonymous(self):
        """
        Страница index отдает кэшированный контент для
        неавторизованного пользователя."""
        post = Post.objects.create(
            text='Тестируем кеш для авторизованного пользователя',
            author=CacheViewsTest.user_cache,
            group=CacheViewsTest.group_cache
        )
        response = self.guest_client.get(reverse('posts:index'))
        content_old = response.content
        post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, content_old)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, content_old)
