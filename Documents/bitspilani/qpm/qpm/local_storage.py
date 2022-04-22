from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.conf import settings
import io
import os
from django.utils import timezone
import shutil


class StaticStorage(StaticFilesStorage):
    # location = 'static'
    pass


class MediaStorage(FileSystemStorage):
    # location = 'media'
    pass


def document_extract_file(QP_doc_path):
    file = os.path.join(settings.MEDIA_ROOT,QP_doc_path )
    with open(file, mode='r+b') as f:
        temp_file = io.BytesIO(f.read())
    return temp_file


def admin_document_extract(filelist=None, doc_uuid=None, email=None,check_box=None):
    if not os.path.exists('/tmp/{}/documents/'.format(doc_uuid)):
        os.makedirs('/tmp/{}/documents/'.format(doc_uuid))
    if check_box=='only_instr':
        for file in filelist:
            if file.alternate_qp_path.name:
                filename = settings.MEDIA_ROOT + '/' + file.alternate_qp_path.name
                shutil.copy(filename, '/tmp/{}/documents/'.format(doc_uuid))
                file.save()

    elif check_box == 'both_qp_and_alternate_qp':
        for file in filelist:
            filename = settings.MEDIA_ROOT + '/' + file.qp_path.name
            file.last_download_datetime = timezone.now()
            file.downloaded_by = email
            shutil.copy(filename, '/tmp/{}/documents/'.format(doc_uuid))
            file.save()

        for file in filelist:
            if file.alternate_qp_path.name:
                filename = settings.MEDIA_ROOT + '/' + file.alternate_qp_path.name
                shutil.copy(filename, '/tmp/{}/documents/'.format(doc_uuid))
                file.save()
    else:
        for file in filelist:
            filename = settings.MEDIA_ROOT + '/' + file.qp_path.name
            file.last_download_datetime = timezone.now()
            file.downloaded_by = email
            shutil.copy(filename, '/tmp/{}/documents/'.format(doc_uuid))
            file.save()
    shutil.make_archive('/tmp/{}/documents/'.format(doc_uuid), 'zip', '/tmp/{}/documents/'.format(doc_uuid))
    return doc_uuid
