# Removes legacy dashboard models; only Productivity* tables remain.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0021_productivity_dashboard"),
    ]

    operations = [
        migrations.DeleteModel(name="CapacityVolume"),
        migrations.DeleteModel(name="WarehouseImportLog"),
        migrations.DeleteModel(name="WarehouseAccountOverview"),
        migrations.DeleteModel(name="DashboardDataCache"),
        migrations.DeleteModel(name="ExcelSheetCache"),
        migrations.DeleteModel(name="InboundShipmentRemark"),
        migrations.DeleteModel(name="MeetingPoint"),
        migrations.DeleteModel(name="UploadMonth"),
        migrations.DeleteModel(name="UploadedFile"),
    ]
