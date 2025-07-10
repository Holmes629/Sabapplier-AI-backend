from django.core.management.base import BaseCommand
from users.models import user, WebsiteAccess

class Command(BaseCommand):
    help = 'Create WebsiteAccess records for existing users who don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable-all',
            action='store_true',
            help='Enable access for all users (use with caution)',
        )

    def handle(self, *args, **options):
        users_without_access = user.objects.filter(website_access__isnull=True)
        
        if not users_without_access.exists():
            self.stdout.write(
                self.style.SUCCESS('All users already have WebsiteAccess records')
            )
            return
        
        created_count = 0
        for usr in users_without_access:
            access_record = WebsiteAccess.objects.create(
                user=usr,
                is_enabled=options['enable_all'],
                notes=f"Auto-created for existing user {'with access enabled' if options['enable_all'] else 'on waitlist'}"
            )
            created_count += 1
            self.stdout.write(f"Created WebsiteAccess for {usr.email}")
        
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
