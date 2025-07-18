from django.core.management.base import BaseCommand
from users.models import user, WebsiteAccess

class Command(BaseCommand):
    help = 'Create WebsiteAccess records for existing users who don\'t have them. First 500 users get access enabled.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable-all',
            action='store_true',
            help='Enable access for all users (use with caution)',
        )

    def handle(self, *args, **options):
        users_without_access = user.objects.filter(website_access__isnull=True).order_by('id')
        
        if not users_without_access.exists():
            self.stdout.write(
                self.style.SUCCESS('All users already have WebsiteAccess records')
            )
            return
        
        created_count = 0
        for idx, usr in enumerate(users_without_access):
            if options['enable_all']:
                is_enabled = True
            else:
                is_enabled = idx < 500  # Enable for first 500 users only
            access_record = WebsiteAccess.objects.create(
                user=usr,
                is_enabled=is_enabled,
                notes=f"Auto-created for existing user {'with access enabled' if is_enabled else 'on waitlist'}"
            )
            created_count += 1
            self.stdout.write(f"Created WebsiteAccess for {usr.email} (is_enabled={is_enabled})")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} WebsiteAccess records')
        )
        
        # Show summary
        total_users = user.objects.count()
        enabled_users = WebsiteAccess.objects.filter(is_enabled=True).count()
        disabled_users = WebsiteAccess.objects.filter(is_enabled=False).count()
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSummary:')
        )
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Users with access: {enabled_users}')
        self.stdout.write(f'Users on waitlist: {disabled_users}')
