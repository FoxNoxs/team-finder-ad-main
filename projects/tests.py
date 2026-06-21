from http import HTTPStatus

from django.test import Client, TestCase

from projects.models import Project
from users.models import User


# --- URL эндпоинты ---
URL_ROOT = '/'
URL_PROJECT_LIST = '/projects/list/'
URL_FAVORITES = '/projects/favorites/'
URL_CREATE_PROJECT = '/projects/create-project/'
URL_REGISTER = '/users/register/'
URL_LOGIN = '/users/login/'
URL_LOGOUT = '/users/logout/'
URL_USERS_LIST = '/users/list/'
URL_EDIT_PROFILE = '/users/edit-profile/'
URL_CHANGE_PASSWORD = '/users/change-password/'

URL_FILTER_FAVORITE_OWNERS = (
    '/users/list/?filter=owners-of-favorite-projects'
)
URL_FILTER_PARTICIPANTS_OF_MY = (
    '/users/list/?filter=participants-of-my-projects'
)


# --- Параметры пагинации ---
PAGINATION_PAGE_SIZE = 12
PAGINATION_TEST_PROJECTS_COUNT = 15


# --- Статусы проектов ---
STATUS_OPEN = 'open'
STATUS_CLOSED = 'closed'


# --- Тестовые пользователи ---
TEST_PASSWORD = 'testpass123'
SECOND_PASSWORD = 'pass123'
NEW_PASSWORD = 'newpass123'
WRONG_PASSWORD = 'wrong'

TEST_EMAIL = 'test@test.com'
OWNER_EMAIL = 'owner@test.com'
OTHER_EMAIL = 'other@test.com'
FAV_EMAIL = 'fav@test.com'
CREATOR_EMAIL = 'creator@test.com'
USER1_EMAIL = 'user1@test.com'
NEW_EMAIL = 'new@test.com'
U1_EMAIL = 'u1@test.com'
U2_EMAIL = 'u2@test.com'

TEST_NAME = 'Test'
TEST_SURNAME = 'User'


# --- Названия проектов ---
TEST_PROJECT_NAME = 'Test Project'
DETAIL_PROJECT_NAME = 'Detail Project'
FAV_PROJECT_NAME = 'Fav Project'
NEW_PROJECT_NAME = 'New Project'
SIMPLE_PROJECT_NAME = 'P1'
PROJECT_NAME_PATTERN = 'Project {index}'


# --- Описания проектов ---
DESC_SIMPLE = 'Test'
DESC_DETAIL = 'Desc'
DESC_NEW = 'New desc'


# --- Прочие пути ---
NONEXISTENT_PROJECT_URL = '/projects/99999/'
COMPLETE_PROJECT_URL = '/projects/{project_id}/complete/'
TOGGLE_PARTICIPATE_URL = '/projects/{project_id}/toggle-participate/'
TOGGLE_FAVORITE_URL = '/projects/{project_id}/toggle-favorite/'
PROJECT_DETAIL_URL = '/projects/{project_id}/'
USER_DETAIL_URL = '/users/{user_id}/'


class ProjectListTests(TestCase):
    """Тесты главной страницы."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=TEST_EMAIL,
            name=TEST_NAME,
            surname=TEST_SURNAME,
            password=TEST_PASSWORD,
        )
        self.project = Project.objects.create(
            name=TEST_PROJECT_NAME,
            description=DESC_SIMPLE,
            owner=self.user,
            status=STATUS_OPEN,
        )
        self.project.participants.add(self.user)

    def test_project_list_accessible(self):
        response = self.client.get(URL_PROJECT_LIST)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_project_list_contains_project(self):
        response = self.client.get(URL_PROJECT_LIST)
        self.assertContains(response, TEST_PROJECT_NAME)

    def test_root_redirects_to_project_list(self):
        response = self.client.get(URL_ROOT)
        self.assertRedirects(response, URL_PROJECT_LIST)

    def test_project_list_pagination(self):
        for i in range(PAGINATION_TEST_PROJECTS_COUNT):
            Project.objects.create(
                name=PROJECT_NAME_PATTERN.format(index=i),
                owner=self.user,
                status=STATUS_OPEN,
            )
        response = self.client.get(URL_PROJECT_LIST)
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            PAGINATION_PAGE_SIZE,
        )


class ProjectDetailTests(TestCase):
    """Тесты страницы проекта."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=OWNER_EMAIL,
            name='Owner',
            surname=TEST_NAME,
            password=TEST_PASSWORD,
        )
        self.other_user = User.objects.create_user(
            email=OTHER_EMAIL,
            name='Other',
            surname=TEST_SURNAME,
            password=TEST_PASSWORD,
        )
        self.project = Project.objects.create(
            name=DETAIL_PROJECT_NAME,
            description=DESC_DETAIL,
            owner=self.user,
            status=STATUS_OPEN,
        )
        self.project.participants.add(self.user)

    def test_project_detail_accessible(self):
        response = self.client.get(
            PROJECT_DETAIL_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_project_404_for_nonexistent(self):
        response = self.client.get(NONEXISTENT_PROJECT_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_complete_project(self):
        self.client.login(username=OWNER_EMAIL, password=TEST_PASSWORD)
        response = self.client.post(
            COMPLETE_PROJECT_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, STATUS_CLOSED)

    def test_complete_project_not_owner(self):
        self.client.login(username=OTHER_EMAIL, password=TEST_PASSWORD)
        response = self.client.post(
            COMPLETE_PROJECT_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_toggle_participate(self):
        self.client.login(username=OTHER_EMAIL, password=TEST_PASSWORD)
        response = self.client.post(
            TOGGLE_PARTICIPATE_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.other_user, self.project.participants.all())

    def test_toggle_participate_remove(self):
        self.client.login(username=OTHER_EMAIL, password=TEST_PASSWORD)
        self.project.participants.add(self.other_user)
        response = self.client.post(
            TOGGLE_PARTICIPATE_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn(self.other_user, self.project.participants.all())


class FavoriteTests(TestCase):
    """Тесты избранного (Вариант 1)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=FAV_EMAIL,
            name='Fav',
            surname=TEST_SURNAME,
            password=TEST_PASSWORD,
        )
        self.project = Project.objects.create(
            name=FAV_PROJECT_NAME,
            owner=self.user,
            status=STATUS_OPEN,
        )

    def test_toggle_favorite_add(self):
        self.client.login(username=FAV_EMAIL, password=TEST_PASSWORD)
        response = self.client.post(
            TOGGLE_FAVORITE_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(data['favorited'])
        self.assertIn(self.project, self.user.favorites.all())

    def test_toggle_favorite_remove(self):
        self.client.login(username=FAV_EMAIL, password=TEST_PASSWORD)
        self.user.favorites.add(self.project)
        response = self.client.post(
            TOGGLE_FAVORITE_URL.format(project_id=self.project.pk)
        )
        data = response.json()
        self.assertFalse(data['favorited'])
        self.assertNotIn(self.project, self.user.favorites.all())

    def test_favorites_page_requires_login(self):
        response = self.client.get(URL_FAVORITES)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_favorites_page_shows_favorites(self):
        self.client.login(username=FAV_EMAIL, password=TEST_PASSWORD)
        self.user.favorites.add(self.project)
        response = self.client.get(URL_FAVORITES)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, FAV_PROJECT_NAME)

    def test_toggle_favorite_requires_login(self):
        response = self.client.post(
            TOGGLE_FAVORITE_URL.format(project_id=self.project.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class CreateProjectTests(TestCase):
    """Тесты создания проекта."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=CREATOR_EMAIL,
            name='Creator',
            surname=TEST_NAME,
            password=TEST_PASSWORD,
        )

    def test_create_project_requires_login(self):
        response = self.client.get(URL_CREATE_PROJECT)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_project_get(self):
        self.client.login(username=CREATOR_EMAIL, password=TEST_PASSWORD)
        response = self.client.get(URL_CREATE_PROJECT)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_project_post(self):
        self.client.login(username=CREATOR_EMAIL, password=TEST_PASSWORD)
        response = self.client.post(URL_CREATE_PROJECT, {
            'name': NEW_PROJECT_NAME,
            'description': DESC_NEW,
            'status': STATUS_OPEN,
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Project.objects.filter(name=NEW_PROJECT_NAME).exists())
        project = Project.objects.get(name=NEW_PROJECT_NAME)
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())


class UserTests(TestCase):
    """Тесты пользователей."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=USER1_EMAIL,
            name='User1',
            surname=TEST_NAME,
            password=TEST_PASSWORD,
        )

    def test_register(self):
        response = self.client.post(URL_REGISTER, {
            'name': 'New',
            'surname': TEST_SURNAME,
            'email': NEW_EMAIL,
            'password': NEW_PASSWORD,
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(User.objects.filter(email=NEW_EMAIL).exists())

    def test_register_duplicate_email(self):
        response = self.client.post(URL_REGISTER, {
            'name': 'Dup',
            'surname': TEST_SURNAME,
            'email': USER1_EMAIL,
            'password': NEW_PASSWORD,
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_success(self):
        response = self.client.post(URL_LOGIN, {
            'email': USER1_EMAIL,
            'password': TEST_PASSWORD,
        })
        self.assertRedirects(response, URL_PROJECT_LIST)

    def test_login_wrong_password(self):
        response = self.client.post(URL_LOGIN, {
            'email': USER1_EMAIL,
            'password': WRONG_PASSWORD,
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout(self):
        self.client.login(username=USER1_EMAIL, password=TEST_PASSWORD)
        response = self.client.get(URL_LOGOUT)
        self.assertRedirects(response, URL_PROJECT_LIST)

    def test_user_detail(self):
        response = self.client.get(
            USER_DETAIL_URL.format(user_id=self.user.pk)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_participants_list(self):
        response = self.client.get(URL_USERS_LIST)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_profile_requires_login(self):
        response = self.client.get(URL_EDIT_PROFILE)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_change_password_requires_login(self):
        response = self.client.get(URL_CHANGE_PASSWORD)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class FilterTests(TestCase):
    """Тесты фильтрации пользователей (Вариант 1)."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email=U1_EMAIL,
            name='U1',
            surname='T',
            password=SECOND_PASSWORD,
        )
        self.user2 = User.objects.create_user(
            email=U2_EMAIL,
            name='U2',
            surname='T',
            password=SECOND_PASSWORD,
        )
        self.project = Project.objects.create(
            name=SIMPLE_PROJECT_NAME,
            owner=self.user2,
            status=STATUS_OPEN,
        )
        self.project.participants.add(self.user2)

    def test_filter_owners_of_favorite_projects(self):
        self.client.login(username=U1_EMAIL, password=SECOND_PASSWORD)
        self.user1.favorites.add(self.project)
        response = self.client.get(URL_FILTER_FAVORITE_OWNERS)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.user2, response.context['page_obj'].object_list)

    def test_filter_participants_of_my_projects(self):
        self.client.login(username=U2_EMAIL, password=SECOND_PASSWORD)
        self.project.participants.add(self.user1)
        response = self.client.get(URL_FILTER_PARTICIPANTS_OF_MY)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.user1, response.context['page_obj'].object_list)
