from pyramid.view import view_config
import sqlalchemy as sa
import wtforms

from occams.utils.forms import Form
from occams_datastore import models as datastore
from occams_forms.renderers import form2json, version2json

from .. import models


@view_config(
    route_name='studies.settings',
    permission='admin',
    renderer='../templates/settings/view.pt')
def view(context, request):
    return {}


# TODO: cleverly join this with the other available_schmata running around
@view_config(
    route_name='studies.settings',
    permission='admin',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
def available_schemata(context, request):
    """
    Returns a listing of available schemata for the study

    The results will try to exclude schemata configured for patients,
    or schemata that is currently used by the context study (if editing).

    GET parameters:
        term -- (optional) filters by schema title or publish date
        schema -- (optional) only shows results for specific schema name
                  (useful for searching for a schema's publish dates)
        grouped -- (optional) groups all results by schema name
    """
    db_session = request.db_session

    class SearchForm(Form):
        term = wtforms.StringField()
        schema = wtforms.StringField()
        grouped = wtforms.BooleanField()

    form = SearchForm(request.GET)
    form.validate()

    query = (
        db_session.query(datastore.Schema)
        .filter(datastore.Schema.publish_date != sa.null())
        .filter(datastore.Schema.retract_date == sa.null())
        .filter(~datastore.Schema.name.in_(
            # Exclude study forms
            db_session.query(datastore.Schema.name)
            .join(models.study_schema_table)
            .union(
                # Exclude randomzation forms
                db_session.query(datastore.Schema.name)
                .join(models.Study.randomization_schema),

                # Exclude termination forms
                db_session.query(datastore.Schema.name)
                .join(models.Study.termination_schema),

                # Exclude already selected patient forms
                db_session.query(datastore.Schema.name)
                .join(models.patient_schema_table))
            .correlate(None)
            .subquery())))

    if form.schema.data:
        query = query.filter(datastore.Schema.name == form.schema.data)

    if form.term.data:
        wildcard = u'%' + form.term.data + u'%'
        query = query.filter(
            datastore.Schema.title.ilike(wildcard)
            | sa.cast(datastore.Schema.publish_date,
                      sa.Unicode).ilike(wildcard))

    query = (
        query.order_by(
            datastore.Schema.title,
            datastore.Schema.publish_date.asc())
        .limit(100))

    return {
        '__query__': form.data,
        'schemata': (form2json(query)
                     if form.grouped.data
                     else [version2json(i) for i in query])
    }
