from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0019_alter_warehouseaccountoverview_capacity_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="warehouseaccountoverview",
            name="capacity_raw",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="warehouseaccountoverview",
            name="clearance_raw",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="warehouseaccountoverview",
            name="inbound_raw",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="warehouseaccountoverview",
            name="outbound_raw",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="warehouseaccountoverview",
            name="transportation_raw",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="warehouseaccountoverview",
            name="occupied_location_raw",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
