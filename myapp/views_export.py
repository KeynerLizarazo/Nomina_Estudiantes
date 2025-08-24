from django.http import HttpResponse
from import_export.formats.base_formats import XLSX, XLS, CSV
from .resources import PersonResource, TutorsResource
from .models import Person, Tutors

def export_persons(request):
    format_param = request.GET.get('format', 'xlsx')
    resource = PersonResource()
    dataset = resource.export(Person.objects.all())
    if format_param == 'csv':
        file_format = CSV()
        content_type = 'text/csv'
        ext = 'csv'
    elif format_param == 'xls':
        file_format = XLS()
        content_type = 'application/vnd.ms-excel'
        ext = 'xls'
    else:
        file_format = XLSX()
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    data = file_format.export_data(dataset)
    response = HttpResponse(data, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="personas.{ext}"'
    return response

def export_tutors(request):
    format_param = request.GET.get('format', 'xlsx')
    resource = TutorsResource()
    dataset = resource.export(Tutors.objects.all())
    if format_param == 'csv':
        file_format = CSV()
        content_type = 'text/csv'
        ext = 'csv'
    elif format_param == 'xls':
        file_format = XLS()
        content_type = 'application/vnd.ms-excel'
        ext = 'xls'
    else:
        file_format = XLSX()
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    data = file_format.export_data(dataset)
    response = HttpResponse(data, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="docentes.{ext}"'
    return response
