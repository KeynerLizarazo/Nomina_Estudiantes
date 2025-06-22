from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),  # Dependencia de la migración anterior
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('apellido', models.CharField(max_length=50)),
                ('documento', models.CharField(max_length=20, unique=True)),
                ('correo', models.EmailField(max_length=254, unique=True)),
                ('username', models.CharField(max_length=50, unique=True)),
                ('contraseña', models.CharField(max_length=100)),
            ],
        ),
    ]