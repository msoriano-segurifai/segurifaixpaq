"""
Tests for Services app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from apps.users.models import User
from apps.services.models import ServiceCategory, ServicePlan, UserService
from datetime import date, timedelta


class ServiceModelTest(TestCase):
    """Test Service models"""

    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name='Test Service',
            category_type=ServiceCategory.CategoryType.ROADSIDE,
            description='Test description',
            is_active=True
        )
        self.plan = ServicePlan.objects.create(
            category=self.category,
            name='Test Plan',
            description='Test plan description',
            price_monthly=99.00,
            price_yearly=990.00,
            max_requests_per_month=5,
            is_active=True
        )

    def test_create_category(self):
        """Test creating a service category"""
        self.assertEqual(self.category.name, 'Test Service')
        self.assertEqual(self.category.category_type, ServiceCategory.CategoryType.ROADSIDE)

    def test_create_plan(self):
        """Test creating a service plan"""
        self.assertEqual(self.plan.name, 'Test Plan')
        self.assertEqual(float(self.plan.price_monthly), 99.00)


class ServiceAPITest(APITestCase):
    """Test Service API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='UserPass123!',
            first_name='Test',
            last_name='User',
            phone_number='+525511111111'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.category = ServiceCategory.objects.create(
            name='Roadside Assistance',
            category_type=ServiceCategory.CategoryType.ROADSIDE,
            description='Roadside help',
            is_active=True
        )
        self.plan = ServicePlan.objects.create(
            category=self.category,
            name='Basic Plan',
            description='Basic roadside assistance',
            price_monthly=99.00,
            price_yearly=990.00,
            max_requests_per_month=5,
            is_active=True,
            is_featured=False
        )

    def test_list_categories_public(self):
        """Test listing categories without authentication"""
        url = reverse('service-category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_category_detail(self):
        """Test getting category details"""
        url = reverse('service-category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Roadside Assistance')

    def test_list_plans_public(self):
        """Test listing plans without authentication"""
        url = reverse('service-plan-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_plan_detail(self):
        """Test getting plan details"""
        url = reverse('service-plan-detail', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Basic Plan')

    def test_get_featured_plans(self):
        """Test getting featured plans"""
        url = reverse('service-plan-featured')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_subscribe_to_plan(self):
        """Test subscribing to a plan"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-service-list')
        data = {'plan': self.plan.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserService.objects.filter(user=self.user, plan=self.plan).exists())

    def test_get_my_subscriptions(self):
        """Test getting user's subscriptions"""
        UserService.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserService.Status.ACTIVE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365)
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('user-service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_create_category_as_admin(self):
        """Test creating category as admin"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('service-category-list')
        data = {
            'name': 'New Service',
            'category_type': 'HEALTH',
            'description': 'Health assistance',
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_plan_as_admin(self):
        """Test creating plan as admin"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('service-plan-list')
        data = {
            'category': self.category.id,
            'name': 'Premium Plan',
            'description': 'Premium service',
            'price_monthly': '199.00',
            'price_yearly': '1990.00',
            'max_requests_per_month': 10,
            'coverage_amount': '5000.00',
            'features': ['Feature 1', 'Feature 2'],
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
