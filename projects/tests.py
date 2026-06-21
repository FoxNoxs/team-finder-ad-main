from django.test import TestCase, Client
from users.models import User
from projects.models import Project


class ProjectListTests(TestCase):
    """Тесты главной страницы."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com', name='Test', surname='User', password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project', description='Test', owner=self.user, status='open'
        )
        self.project.participants.add(self.user)

    def test_project_list_accessible(self):
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)

    def test_project_list_contains_project(self):
        response = self.client.get('/projects/list/')
        self.assertContains(response, 'Test Project')

    def test_root_redirects_to_project_list(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/projects/list/')

    def test_project_list_pagination(self):
        for i in range(15):
            Project.objects.create(
                name=f'Project {i}', owner=self.user, status='open'
            )
        response = self.client.get('/projects/list/')
        self.assertEqual(len(response.context['page_obj'].object_list), 12)


class ProjectDetailTests(TestCase):
    """Тесты страницы проекта."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='owner@test.com', name='Owner', surname='Test', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@test.com', name='Other', surname='User', password='testpass123'
        )
        self.project = Project.objects.create(
            name='Detail Project', description='Desc', owner=self.user, status='open'
        )
        self.project.participants.add(self.user)

    def test_project_detail_accessible(self):
        response = self.client.get(f'/projects/{self.project.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_project_404_for_nonexistent(self):
        response = self.client.get('/projects/99999/')
        self.assertEqual(response.status_code, 404)

    def test_complete_project(self):
        self.client.login(username='owner@test.com', password='testpass123')
        response = self.client.post(f'/projects/{self.project.pk}/complete/')
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

    def test_complete_project_not_owner(self):
        self.client.login(username='other@test.com', password='testpass123')
        response = self.client.post(f'/projects/{self.project.pk}/complete/')
        self.assertEqual(response.status_code, 403)

    def test_toggle_participate(self):
        self.client.login(username='other@test.com', password='testpass123')
        response = self.client.post(f'/projects/{self.project.pk}/toggle-participate/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.other_user, self.project.participants.all())

    def test_toggle_participate_remove(self):
        self.client.login(username='other@test.com', password='testpass123')
        self.project.participants.add(self.other_user)
        response = self.client.post(f'/projects/{self.project.pk}/toggle-participate/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.other_user, self.project.participants.all())


class FavoriteTests(TestCase):
    """Тесты избранного (Вариант 1)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='fav@test.com', name='Fav', surname='User', password='testpass123'
        )
        self.project = Project.objects.create(
            name='Fav Project', owner=self.user, status='open'
        )

    def test_toggle_favorite_add(self):
        self.client.login(username='fav@test.com', password='testpass123')
        response = self.client.post(f'/projects/{self.project.pk}/toggle-favorite/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['favorited'])
        self.assertIn(self.project, self.user.favorites.all())

    def test_toggle_favorite_remove(self):
        self.client.login(username='fav@test.com', password='testpass123')
        self.user.favorites.add(self.project)
        response = self.client.post(f'/projects/{self.project.pk}/toggle-favorite/')
        data = response.json()
        self.assertFalse(data['favorited'])
        self.assertNotIn(self.project, self.user.favorites.all())

    def test_favorites_page_requires_login(self):
        response = self.client.get('/projects/favorites/')
        self.assertEqual(response.status_code, 302)

    def test_favorites_page_shows_favorites(self):
        self.client.login(username='fav@test.com', password='testpass123')
        self.user.favorites.add(self.project)
        response = self.client.get('/projects/favorites/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fav Project')

    def test_toggle_favorite_requires_login(self):
        response = self.client.post(f'/projects/{self.project.pk}/toggle-favorite/')
        self.assertEqual(response.status_code, 302)


class CreateProjectTests(TestCase):
    """Тесты создания проекта."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='creator@test.com', name='Creator', surname='Test', password='testpass123'
        )

    def test_create_project_requires_login(self):
        response = self.client.get('/projects/create-project/')
        self.assertEqual(response.status_code, 302)

    def test_create_project_get(self):
        self.client.login(username='creator@test.com', password='testpass123')
        response = self.client.get('/projects/create-project/')
        self.assertEqual(response.status_code, 200)

    def test_create_project_post(self):
        self.client.login(username='creator@test.com', password='testpass123')
        response = self.client.post('/projects/create-project/', {
            'name': 'New Project',
            'description': 'New desc',
            'status': 'open',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name='New Project').exists())
        project = Project.objects.get(name='New Project')
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())


class UserTests(TestCase):
    """Тесты пользователей."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='user1@test.com', name='User1', surname='Test', password='testpass123'
        )

    def test_register(self):
        response = self.client.post('/users/register/', {
            'name': 'New', 'surname': 'User',
            'email': 'new@test.com', 'password': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_register_duplicate_email(self):
        response = self.client.post('/users/register/', {
            'name': 'Dup', 'surname': 'User',
            'email': 'user1@test.com', 'password': 'newpass123',
        })
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post('/users/login/', {
            'email': 'user1@test.com', 'password': 'testpass123',
        })
        self.assertRedirects(response, '/projects/list/')

    def test_login_wrong_password(self):
        response = self.client.post('/users/login/', {
            'email': 'user1@test.com', 'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username='user1@test.com', password='testpass123')
        response = self.client.get('/users/logout/')
        self.assertRedirects(response, '/projects/list/')

    def test_user_detail(self):
        response = self.client.get(f'/users/{self.user.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_participants_list(self):
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_requires_login(self):
        response = self.client.get('/users/edit-profile/')
        self.assertEqual(response.status_code, 302)

    def test_change_password_requires_login(self):
        response = self.client.get('/users/change-password/')
        self.assertEqual(response.status_code, 302)


class FilterTests(TestCase):
    """Тесты фильтрации пользователей (Вариант 1)."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='u1@test.com', name='U1', surname='T', password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='u2@test.com', name='U2', surname='T', password='pass123'
        )
        self.project = Project.objects.create(
            name='P1', owner=self.user2, status='open'
        )
        self.project.participants.add(self.user2)

    def test_filter_owners_of_favorite_projects(self):
        self.client.login(username='u1@test.com', password='pass123')
        self.user1.favorites.add(self.project)
        response = self.client.get('/users/list/?filter=owners-of-favorite-projects')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user2, response.context['page_obj'].object_list)

    def test_filter_participants_of_my_projects(self):
        self.client.login(username='u2@test.com', password='pass123')
        self.project.participants.add(self.user1)
        response = self.client.get('/users/list/?filter=participants-of-my-projects')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user1, response.context['page_obj'].object_list)