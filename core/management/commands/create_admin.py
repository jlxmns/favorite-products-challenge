from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser for testing'

    def handle(self, *args, **options):
        name = 'admin'
        email = 'admin@aiqfome.com'
        password = 'admin'

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
        else:
            User.objects.create_superuser(
                email=email,
                password=password,
                name=name
            )
            self.stdout.write(self.style.SUCCESS('Admin user created successfully'))
