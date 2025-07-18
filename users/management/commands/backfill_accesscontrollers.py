from django.core.management.base import BaseCommand
from users.models import user, AccessController

class Command(BaseCommand):
    help = 'Create AccessController entries for all users who do not have one. First 500 users get has_website_access=True (and user field updated to match).'

    def handle(self, *args, **options):
        users_without_ac = user.objects.filter(access_controllers__isnull=True).order_by('id')
        created_count = 0
        for idx, u in enumerate(users_without_ac):
            has_access = idx < 500
            AccessController.objects.create(
                email=u,
                force_advanced_locked=u.force_advanced_locked,
                has_website_access=has_access,
                referral_code=u.referral_code,
                referred_by=u.referred_by,
                successful_referrals=u.successful_referrals,
            )
            # Also update the user model field
            u.has_website_access = has_access
            u.save(update_fields=["has_website_access"])
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created AccessController for {u.email} (has_website_access={has_access}) and updated user field."))
        if created_count == 0:
            self.stdout.write(self.style.WARNING('All users already have AccessController entries.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} AccessController entries and updated user fields.')) 