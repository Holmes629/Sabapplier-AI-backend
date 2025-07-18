from django.core.management.base import BaseCommand
from users.models import user
import uuid

class Command(BaseCommand):
    help = 'Generate referral codes for users who do not have one.'

    def handle(self, *args, **options):
        updated = 0
        for u in user.objects.filter(referral_code__isnull=True):
            code = str(uuid.uuid4())[:8]
            # Ensure uniqueness
            while user.objects.filter(referral_code=code).exists():
                code = str(uuid.uuid4())[:8]
            u.referral_code = code
            u.save()
            updated += 1
            self.stdout.write(self.style.SUCCESS(f'Assigned referral code {code} to user {u.email}'))
        if updated == 0:
            self.stdout.write(self.style.WARNING('All users already have referral codes.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} users with new referral codes.')) 