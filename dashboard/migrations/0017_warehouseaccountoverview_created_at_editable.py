# Generated manually: جعل created_at قابلاً للتعديل (إضافة/تعديل التواريخ من الأدمن)

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_alter_warehouseaccountoverview_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='warehouseaccountoverview',
            name='created_at',
            field=models.DateTimeField(default=timezone.now),
        ),
    ]
