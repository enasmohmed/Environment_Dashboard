# Generated manually: تسجيل آخر استيراد إكسل لاستخدام تاريخه كافتراضي

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_warehouseaccountoverview_created_at_editable'),
    ]

    operations = [
        migrations.CreateModel(
            name='WarehouseImportLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effective_date', models.DateField(db_index=True)),
                ('imported_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Warehouse Import Log',
                'verbose_name_plural': 'Warehouse Import Logs',
                'ordering': ('-imported_at',),
            },
        ),
    ]
