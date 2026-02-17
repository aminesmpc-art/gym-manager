from django.db import models


class Grade(models.Model):
    """
    Predefined grade / class level for a school tenant.
    Stored per-tenant (django-tenants isolates schemas automatically).
    """
    name = models.CharField(max_length=100, unique=True)
    order = models.IntegerField(default=0, help_text='Sort order (lower = first)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
