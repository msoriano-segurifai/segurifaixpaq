from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with role-based access"""

    class Role(models.TextChoices):
        # SegurifAI Platform Roles (owns all, can view everything)
        ADMIN = 'ADMIN', _('SegurifAI Super Admin')
        SEGURIFAI_TEAM = 'SEGURIFAI_TEAM', _('SegurifAI Team Member')
        # End User
        USER = 'USER', _('User')
        # Provider (legacy - for backwards compatibility)
        PROVIDER = 'PROVIDER', _('Assistance Provider')
        # MAWDY Organization Roles
        MAWDY_ADMIN = 'MAWDY_ADMIN', _('MAWDY Administrator')
        MAWDY_FIELD_TECH = 'MAWDY_FIELD_TECH', _('MAWDY Field Technician')
        # PAQ Organization Roles
        PAQ_ADMIN = 'PAQ_ADMIN', _('PAQ Administrator')

    class Gender(models.TextChoices):
        MALE = 'M', _('Masculino')
        FEMALE = 'F', _('Femenino')
        OTHER = 'O', _('Otro')
        NOT_SPECIFIED = 'N', _('Prefiero no decir')

    # Basic Information
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone_number = models.CharField(_('phone number'), max_length=20)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=1, choices=Gender.choices, blank=True)

    # Role
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )

    # Additional Information
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    country = models.CharField(_('country'), max_length=100, default='Mexico')

    # Emergency Contact
    emergency_contact_name = models.CharField(_('emergency contact name'), max_length=150, blank=True)
    emergency_contact_phone = models.CharField(_('emergency contact phone'), max_length=20, blank=True)

    # PAQ Wallet Integration
    paq_wallet_id = models.CharField(_('PAQ Wallet ID'), max_length=100, blank=True, unique=True, null=True)

    # Profile Image
    profile_image = models.ImageField(_('profile image'), upload_to='profiles/', blank=True, null=True)

    # Status flags
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_phone_verified = models.BooleanField(_('phone verified'), default=False)

    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_login_at = models.DateTimeField(_('last login at'), null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    @property
    def is_admin(self):
        """Check if user is a SegurifAI super admin"""
        return self.role == self.Role.ADMIN

    @property
    def is_segurifai_team(self):
        """Check if user is SegurifAI team (admin or team member)"""
        return self.role in [self.Role.ADMIN, self.Role.SEGURIFAI_TEAM]

    @property
    def is_provider(self):
        """Check if user is a provider"""
        return self.role == self.Role.PROVIDER

    @property
    def is_regular_user(self):
        """Check if user is a regular user"""
        return self.role == self.Role.USER

    @property
    def is_mawdy_admin(self):
        """Check if user is MAWDY admin"""
        return self.role == self.Role.MAWDY_ADMIN

    @property
    def is_mawdy_team(self):
        """Check if user is part of MAWDY team (admin, field tech, or provider)"""
        return self.role in [self.Role.MAWDY_ADMIN, self.Role.MAWDY_FIELD_TECH, self.Role.PROVIDER]

    @property
    def is_paq_admin(self):
        """Check if user is PAQ admin"""
        return self.role == self.Role.PAQ_ADMIN

    @property
    def can_view_all_reports(self):
        """Check if user can view all reports (SegurifAI team only)"""
        return self.role in [self.Role.ADMIN, self.Role.SEGURIFAI_TEAM]
