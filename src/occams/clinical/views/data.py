import os.path
from pkg_resources import resource_filename

import colander
import deform
from pyramid_deform import CSRFSchema
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import FileResponse
from pyramid.security import authenticated_userid
from pyramid.view import view_config
from sqlalchemy import orm, null
import transaction

from occams.clinical import _, models, Session, tasks


def existent_schema_validator(value):
    """
    Deferred validator to determine the schema choices at request-time.
    """
    if not value:
        return _(u'No schemata specified')
    ids_query = (
        Session.query(models.Schema.id)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.id.in_(value)))
    if ids_query.count() != len(value):
        return _(u'Invalid schemata chosen')
    return True


class ExportCheckoutSchema(CSRFSchema):
    """
    Export checkout serialization schema
    """

    @colander.instantiate(
        validator=colander.Function(existent_schema_validator))
    class schemata(colander.SequenceSchema):

        id = colander.SchemaNode(colander.Int())


@view_config(
    route_name='data_list',
    permission='fia_view',
    renderer='occams.clinical:templates/data/list.pt')
def list_(request):
    """
    List data that is available for download

    Becuase the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is then queued in a another thread so the user
    isn't left with an unresponsive page.
    """
    userid = authenticated_userid(request)
    schema = ExportCheckoutSchema().bind(request=request)
    form = deform.Form(schema)

    if request.method == 'POST':
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as form:
            pass
        else:
            with transaction.manager:
                export = models.Export(
                    owner_user=(
                        Session.query(models.User)
                        .filter_by(key=userid)
                        .one()),
                    schemata=(
                        Session.query(models.Schema)
                        .filter(models.Schema.id.in_(appstruct['schemata']))
                        .all()))
                Session.add(export)
                Session.flush()
                export_id = export.id
            tasks.make_export.s(export_id).apply_async(
                link_error=tasks.handle_error.s())
            request.session.flash(
                _(u'Your request has been received!'), 'success')
            return HTTPFound(location=request.route_path('data_download'))

    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    schemata_query = (
        Session.query(models.Schema)
        .filter(models.Schema.publish_date != null())
        .order_by(
            models.Schema.name.asc(),
            models.Schema.publish_date.desc()))

    schemata_count = schemata_query.count()

    return {
        'csrf_token': request.session.get_csrf_token(),
        'form': form,
        'schemata': schemata_query,
        'has_schemata': schemata_count > 0,
        'schemata_count': schemata_count}


@view_config(
    route_name='data_download',
    permission='fia_view',
    renderer='occams.clinical:templates/data/download.pt')
def download(request):
    """
    Lists current export jobs.

    This is where the user can view the progress of the exports and download
    them at a later time.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')
    userid = authenticated_userid(request)

    exports_query = (
        Session.query(models.Export)
        .filter(models.Export.owner_user.has(key=userid))
        .order_by(models.Export.create_date.desc()))

    exports_count = exports_query.count()

    return {
        'duration': '1 week',
        'exports': exports_query,
        'exports_count': exports_count,
        'has_exports': exports_count > 0}


@view_config(
    route_name='data_download',
    permission='fia_view',
    request_method='GET',
    request_param='id')
def attachement(request):
    """
    Returns specific download attachement
    The user should only be allowed to download their exports.
    """
    userid = authenticated_userid(request)
    try:
        export = (
            Session.query(models.Export)
            .filter_by(id=request.GET['id'], status='complete')
            .filter(models.Export.owner_user.has(key=userid))
            .one())
    except orm.exc.NoResultFound:
        raise HTTPNotFound

    export_dir = resource_filename('occams.clinical', 'exports')
    path = os.path.join(export_dir, '%s.zip' % export.id)

    response = FileResponse(path)
    response.content_disposition = (
        'attachment;filename=clinical-%d.zip' % export.id)
    return response
