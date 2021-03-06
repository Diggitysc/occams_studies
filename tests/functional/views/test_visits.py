import pytest
from occams.testing import USERID, make_environ, get_csrf_token


class TestPermissionsVisitsView:

    url = '/studies/patients/123/visits'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            db_session.add(study)
            db_session.add(patient)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.get(self.url, status=401, xhr=True)


class TestPermissionsVisitsAdd:

    url = '/studies/patients/123/visits'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(cycle)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        cycle_id = db_session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-01',
            'include_forms': False,
            'include_speciman': False
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        cycle_id = db_session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-01',
            'include_forms': False,
            'include_speciman': False
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.post(self.url, status=401, xhr=True)


class TestPermissionsVisitView:

    url = '/studies/patients/123/visits/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        res = app.get(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        res = app.get(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()
        app.get(self.url.format(visit_date), status=401, xhr=True)


class TestPermissionsVisitDelete:

    url = '/studies/patients/123/visits/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        res = app.delete(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        res = app.delete(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()
        app.delete(self.url.format(visit_date), status=401, xhr=True)


class TestPermissionsVisitEdit:

    url = '/studies/patients/123/visits/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        cycle_id = db_session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-02'
        }

        res = app.put_json(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        cycle_id = db_session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-02'
        }

        res = app.put_json(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        visit_date = db_session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()
        app.put(self.url.format(visit_date), status=401, xhr=True)


class TestPermissionsVisitFormsAdd:

    url = '/studies/patients/123/visits/2015-01-01/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        data = {
            'schema': form_id,
            'collect_date': '2015-01-01'
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        data = {
            'schema': form_id,
            'collect_date': '2015-01-01'
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.post(self.url, status=401, xhr=True)


class TestPermissionsVisitFormsDelete:

    url = '/studies/patients/123/visits/2015-01-01/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            entity = datastore.Entity(
                schema=form,
                collect_date=date(2015, 1, 1)
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)
            db_session.add(entity)
            patient.entities.add(entity)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        res = app.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={'forms': [entity_id]})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
        'UCSD:member', None])
    def test_not_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.delete(self.url, status=401, xhr=True)


class TestPermissionsVisitFormView:

    url = '/studies/patients/123/visits/2015-01-01/forms/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            entity = datastore.Entity(
                schema=form,
                collect_date=date(2015, 1, 1)
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)
            db_session.add(entity)
            patient.entities.add(entity)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        res = app.get(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        res = app.get(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_datastore import models as datastore

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        app.get(self.url.format(entity_id), status=401)


class TestPermissionsVisitFormEdit:

    url = '/studies/patients/123/visits/2015-01-01/forms/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            entity = datastore.Entity(
                schema=form,
                collect_date=date(2015, 1, 1)
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(visit)
            db_session.add(entity)
            patient.entities.add(entity)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        res = app.post(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        res = app.post(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_datastore import models as datastore

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema').scalar()

        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema_id == form_id).scalar()

        app.post(self.url.format(entity_id), status=401)
