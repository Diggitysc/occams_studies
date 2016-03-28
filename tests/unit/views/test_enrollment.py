import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams_studies.views.enrollment.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestViewJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import view_json as view
        return view(*args, **kw)

    def test_hide_blinded_randomization(self, req, db_session, factories):
        """
        It should not include randomization status if study is blinded
        """

        schema = factories.SchemaFactory.create()

        study = factories.StudyFactory.create(
            randomization_schema=schema,
            is_randomized=True
        )

        enrollment = factories.EnrollmentFactory(
            study=study,
            stratum=factories.StratumFactory(
                arm__study=study
            )
        )

        db_session.flush()

        study.is_blinded = False
        db_session.flush()
        res = self._call_fut(enrollment, req)
        assert res['stratum']['arm'] is not None

        study.is_blinded = True
        db_session.flush()
        res = self._call_fut(enrollment, req)
        assert res['stratum']['arm'] is None


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import edit_json as view
        return view(*args, **kw)

    def test_save(self, req, db_session, factories):
        from datetime import date
        from occams_studies import models

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        db_session.flush()

        today = date.today()

        payload = {
            'study': str(study.id),
            'consent_date': str(today),
            'latest_consent_date': str(today),
            'termination_date': str(today),
            'reference_number': u'123'
        }

        req.json_body = payload
        res = self._call_fut(patient['enrollments'], req)

        enrollment = db_session.query(models.Enrollment).get(res['id'])

        actual = {
            'study': str(enrollment.study.id),
            'consent_date': str(enrollment.consent_date),
            'latest_consent_date': str(enrollment.latest_consent_date),
            'termination_date': str(enrollment.termination_date),
            'reference_number': str(enrollment.reference_number)
        }

        assert payload == actual

    def test_unique_consent(self, req, db_session, factories):
        """
        It should allow multiple enrollments to a study, but a single consent.
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        db_session.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(consent_date),
            'latest_consent_date': str(consent_date),
        }

        self._call_fut(patient['enrollments'], req)

        assert (
            db_session.query(models.Enrollment)
            .filter_by(patient=patient, study=study)
            .one()) is not None

        # Try adding it again, it should fail
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'This enrollment already exists.' in \
            excinfo.value.json['errors']['consent_date']

    def test_missing_consent(self, req, db_session, factories):
        """
        It should require latest date
        """

        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        db_session.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': None,
            'latest_consent_date': str(consent_date),
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'required' in \
            excinfo.value.json['errors']['consent_date']

    def test_missing_latest_consent(self, req, db_session, factories):
        """
        It should require latest consent date
        """

        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        db_session.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(consent_date),
            'latest_consent_date': None
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'required' in \
            excinfo.value.json['errors']['latest_consent_date']

    def test_disable_study_update(self, req, db_session, factories):
        """
        It should not allow a enrollment's study to be changed
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest

        study1 = factories.StudyFactory.create()
        study2 = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        enrollment = factories.EnrollmentFactory.create(
            study=study1,
            patient=patient,
            consent_date=study1.consent_date)
        db_session.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study2.id),
            'consent_date': str(consent_date),
            'latest_consent_date': str(consent_date),
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(enrollment, req)

        assert 'Cannot change an enrollment\'s study.' in \
            excinfo.value.json['errors']['study']

    def test_update_patient(self, req, db_session, factories):
        """
        It should mark the patient as updated
        """
        from datetime import date

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        db_session.flush()

        old_modify_date = patient.modify_date
        req.json_body = {
            'study': study.id,
            'consent_date': str(date.today()),
            'latest_consent_date': str(date.today())
        }

        self._call_fut(patient['enrollments'], req)
        assert old_modify_date < patient.modify_date

    def test_temination_date_disabled_if_form_configured(
            self, req, db_session, factories):
        """
        Termination date is populated via form when available
        """

        from datetime import date, timedelta

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        enrollment = factories.EnrollmentFactory.create(
            study=factories.StudyFactory.create(
                consent_date=t3,
                termination_schema=factories.SchemaFactory.create(
                    publish_date=t1,
                    attributes={
                        'termination_date': factories.AttributeFactory(
                            name='termination_date',
                            type='date'
                        )
                    }
                )
            ),
            patient=factories.PatientFactory.create(),
            consent_date=t1,
            termination_date=t3
        )

        db_session.flush()

        req.json_body = {
            'study': enrollment.study.id,
            'consent_date': str(t1),
            'latest_consent_date': str(t2),
            'termination_date': str(t4)
        }

        self._call_fut(enrollment, req)

        # Termination date should not have changed because
        # it's controlled via termination schema
        assert t3 == enrollment.termination_date

    def test_temination_date_enabled_if_no_termination(
            self, req, db_session, factories):
        """
        Termination date is populated directly through form is unavailable
        """

        from datetime import date, timedelta

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        enrollment = factories.EnrollmentFactory.create(
            study=factories.StudyFactory.create(
                consent_date=t3,
            ),
            patient=factories.PatientFactory.create(),
            consent_date=t1,
            termination_date=t3
        )
        db_session.flush()

        req.json_body = {
            'study': enrollment.study.id,
            'consent_date': str(t1),
            'latest_consent_date': str(t2),
            'termination_date': str(t4)
        }

        self._call_fut(enrollment, req)

        # Termination date should have changed because there
        # is not termination schema that controls it
        assert t4 == enrollment.termination_date


class TestDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import delete_json as view
        return view(*args, **kw)

    def test_update_patient(self, req, db_session, factories):
        """
        It should mark the patient as updated
        """
        enrollment = factories.EnrollmentFactory.create()
        patient = enrollment.patient
        db_session.flush()

        old_modify_date = patient.modify_date
        self._call_fut(enrollment, req)
        assert old_modify_date < patient.modify_date

    def test_cascade_forms(self, req, db_session, factories):
        """
        It should also remove termination forms.
        """
        from occams_datastore import models as datastore
        from occams_studies import models

        enrollment = factories.EnrollmentFactory.create()
        enrollment.entities.add(factories.EntityFactory.create())
        db_session.flush()

        enrollment_id = enrollment.id

        self._call_fut(enrollment, req)

        assert db_session.query(models.Enrollment).get(enrollment_id) is None
        assert 0 == db_session.query(datastore.Entity).count()


class Test_randomization_ajax:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import randomize_ajax as view
        return view(*args, **kw)

    def test_challenge(self, req, db_session, config, factories):
        """
        It should set to CHALLENGE mode when no session is found
        """
        import mock
        from occams_studies.views.enrollment import \
            RAND_INFO_KEY, RAND_CHALLENGE

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )
        db_session.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = None

        self._call_fut(enrollment, req)

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_CHALLENGE

    def test_transition_from_enter_to_verify(
            self, req, db_session, config, factories):
        """
        It should transition from ENTER to VERIFY on successfull submit
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams_studies.views.enrollment import \
            RAND_INFO_KEY, RAND_ENTER, RAND_VERIFY

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_ENTER,
            'formdata': {}
        }
        req.method = 'POST'
        req.POST = MultiDict({'procid': procid})

        self._call_fut(enrollment, req)

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_VERIFY

    def test_transition_from_verify_to_complete(
            self, req, db_session, config, factories):
        """
        It should randomize the patient on successful submit from VERIFY
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams_studies.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        config.include('pyramid_chameleon')
        req.method = 'POST'
        req.POST = MultiDict()

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )
        stratum = factories.StratumFactory(study=enrollment.study)
        stratum.entities.add(factories.EntityFactory.create(
            schema=enrollment.study.randomization_schema
        ))
        db_session.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        self._call_fut(enrollment, req)

        assert RAND_INFO_KEY not in req.session

    def test_randid_assignment(self, req, db_session, config, factories):
        """
        It should assign randomiation ids sequentially
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams_studies.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        config.include('pyramid_chameleon')

        req.method = 'POST'
        req.POST = MultiDict()

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        stratum1 = factories.StratumFactory(study=study)
        stratum1.entities.add(factories.EntityFactory.create(
            schema=study.randomization_schema
        ))
        stratum2 = factories.StratumFactory(study=study)
        stratum2.entities.add(factories.EntityFactory.create(
            schema=study.randomization_schema
        ))

        enrollment1 = factories.EnrollmentFactory.create(study=study)
        enrollment2 = factories.EnrollmentFactory.create(study=study)
        db_session.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        res = self._call_fut(enrollment1, req)

        db_session.refresh(enrollment1)
        assert enrollment1.stratum == stratum1

        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})
        res = self._call_fut(enrollment2, req)

        db_session.refresh(enrollment2)
        assert enrollment2.stratum == stratum2

    def test_randid_assignment_with_criteria(
            self, req, db_session, config, factories):
        """
        It should assign a randid given the criteria associated with a stratum
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams_studies.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        schema = factories.SchemaFactory.create(
            attributes={
                u'likes_icecream': factories.AttributeFactory.create(
                    name=u'likes_icecream',
                    type=u'choice',
                    choices={
                        u'0': factories.ChoiceFactory.create(name=u'0'),
                        u'1': factories.ChoiceFactory.create(name=u'1'),
                    },
                )
            }
        )

        study = factories.StudyFactory.create(
            randomization_schema=schema,
            is_randomized=True
        )

        stratum1 = factories.StratumFactory.create(study=study)
        stratum2 = factories.StratumFactory.create(study=study)

        entity1 = factories.EntityFactory.create(schema=schema)
        entity1['likes_icecream'] = u'0'
        stratum1.entities.add(entity1)

        # If we submit yes, we'll be put into the 'fake sugar' arm of the study
        entity2 = factories.EntityFactory.create(schema=schema)
        entity2['likes_icecream'] = u'1'
        stratum2.entities.add(entity2)

        enrollment = factories.EnrollmentFactory.create(study=study)
        db_session.flush()

        config.include('pyramid_chameleon')

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        payload = {'procid': procid, 'likes_icecream': u'1'}
        req.POST = MultiDict(payload)
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': payload
        }
        res = self._call_fut(enrollment, req)

        db_session.refresh(enrollment)
        assert enrollment.stratum == stratum2
