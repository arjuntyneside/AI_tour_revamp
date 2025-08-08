from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import TourOperator, TourOperatorUser

class Command(BaseCommand):
    help = 'Set up a demo tour operator and associate with superuser'

    def handle(self, *args, **options):
        # Get the first superuser
        try:
            superuser = User.objects.filter(is_superuser=True).first()
            if not superuser:
                self.stdout.write(
                    self.style.ERROR('No superuser found. Please create one first with: python manage.py createsuperuser')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error finding superuser: {e}')
            )
            return

        # Create tour operator
        tour_operator, created = TourOperator.objects.get_or_create(
            email=superuser.email or 'admin@example.com',
            defaults={
                'name': superuser.get_full_name() or superuser.username,
                'company_name': 'Demo Tour Company',
                'phone': '+1234567890',
                'website': 'https://example.com',
                'address': '123 Demo Street, Demo City',
                'subscription_plan': 'professional',
                'subscription_status': 'active',
                'ai_document_processing': True,
                'ai_pricing_analysis': True,
                'ai_demand_forecasting': True,
                'ai_customer_segmentation': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created tour operator: {tour_operator.company_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Tour operator already exists: {tour_operator.company_name}')
            )

        # Create tour operator user association
        tour_operator_user, created = TourOperatorUser.objects.get_or_create(
            user=superuser,
            defaults={
                'tour_operator': tour_operator,
                'role': 'owner',
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Associated user {superuser.username} with tour operator {tour_operator.company_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'User {superuser.username} already associated with tour operator {tour_operator.company_name}')
            )

        self.stdout.write(
            self.style.SUCCESS('Setup complete! You can now login and access the dashboard.')
        )
