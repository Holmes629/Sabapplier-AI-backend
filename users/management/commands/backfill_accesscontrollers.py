from django.core.management.base import BaseCommand
from users.models import user, AccessController

class Command(BaseCommand):
    help = 'Create AccessController entries for all users who do not have one.'

    def handle(self, *args, **options):
        created_count = 0
        for u in user.objects.all():
            if u.access_controllers.count() == 0:
                AccessController.objects.create(
                    email=u,
                    name=f"Access for {u.email}",
                    force_advanced_locked=u.force_advanced_locked,
                    has_website_access=u.has_website_access,
                    referral_code=u.referral_code,
                    referred_by=u.referred_by,
                    successful_referrals=u.successful_referrals,
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created AccessController for {u.email}"))
        if created_count == 0:
            self.stdout.write(self.style.WARNING('All users already have AccessController entries.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} AccessController entries.')) 