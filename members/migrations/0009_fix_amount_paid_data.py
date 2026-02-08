"""
Data migration to fix corrupted amount_paid values.
Recalculates amount_paid from actual Payment records (single source of truth).
"""
from django.db import migrations


def recalculate_amount_paid(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    Payment = apps.get_model('subscriptions', 'Payment')
    
    from django.db.models import Sum
    from decimal import Decimal
    
    for member in Member.objects.all():
        actual_paid = Payment.objects.filter(
            member=member,
            period_start=member.subscription_start,
            period_end=member.subscription_end,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if member.amount_paid != actual_paid:
            member.amount_paid = actual_paid
            member.save(update_fields=['amount_paid'])


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_member_insurance_year_member_whatsapp'),
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            recalculate_amount_paid,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
