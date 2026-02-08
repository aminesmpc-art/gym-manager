"""
Management command to recalculate member amount_paid from Payment records.
Fixes corrupted data from payment doubling bugs.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from members.models import Member
from subscriptions.models import Payment


class Command(BaseCommand):
    help = 'Recalculate amount_paid for all members from their Payment records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        members = Member.objects.all()
        fixed_count = 0
        
        self.stdout.write(f"\nChecking {members.count()} members...\n")

        for member in members:
            # Get sum of payments for current subscription period
            current_payments = Payment.objects.filter(
                member=member,
                period_start=member.subscription_start,
                period_end=member.subscription_end,
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            old_amount = Decimal(str(member.amount_paid))
            new_amount = current_payments

            if old_amount != new_amount:
                plan_price = Decimal(str(member.membership_plan.price)) if member.membership_plan else Decimal('0')
                new_debt = max(plan_price - new_amount, Decimal('0'))
                
                self.stdout.write(
                    f"  {member.full_name}: "
                    f"amount_paid {old_amount} -> {new_amount}, "
                    f"debt {member.remaining_debt} -> {new_debt}"
                )
                
                if not dry_run:
                    member.amount_paid = new_amount
                    member.remaining_debt = new_debt
                    member.save(update_fields=['amount_paid', 'remaining_debt', 'updated_at'])
                
                fixed_count += 1
            else:
                self.stdout.write(f"  {member.full_name}: OK ({old_amount} DH)")

        action = "Would fix" if dry_run else "Fixed"
        self.stdout.write(
            self.style.SUCCESS(f"\n{action} {fixed_count}/{members.count()} members")
        )
