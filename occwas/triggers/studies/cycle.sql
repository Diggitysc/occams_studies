---
--- avrc_data/cycle -> pirc/cycle
---

DROP FOREIGN TABLE IF EXISTS cycle_ext;


CREATE FOREIGN TABLE cycle_ext (
    id              INTEGER NOT NULL

  , zid             INTEGER NOT NULL
  , study_id        INTEGER NOT NULL
  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT
  , week            INTEGER
  , threshold       INTEGER
  , category_id     INTEGER

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'cycle');

DROP FUNCTION IF EXISTS ext_cycle_id(INTEGER);

CREATE OR REPLACE FUNCTION ext_cycle_id(id INTEGER) RETURNS integer AS $$
  BEGIN
    RETURN (
      SELECT "cycle_ext".id
      FROM "cycle_ext"
      WHERE old_db = (SELECT current_database()) AND old_id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION cycle_mirror() RETURNS TRIGGER AS $$
  DECLARE
    ext_id int;
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        SELECT val INTO ext_id FROM dblink('SELECT nextval(''cycle_id_seq'') AS val') AS sec(val int);
        PERFORM dblink_disconnect();

        INSERT INTO "cycle_ext" (
            id
          , zid
          , study_id
          , name
          , title
          , description
          , week
          , threshold
          , category_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            ext_id
          , NEW.zid
          , ext_study_id(NEW.study_id)
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.week
          , NEW.threshold
          , ext_category_id(NEW.category_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM "cycle_ext"
        WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE "cycle_ext"
        SET zid = NEW.zid
          , study_id = ext_study_id(NEW.study_id)
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , week = NEW.week
          , threshold = NEW.threshold
          , category_id = ext_category_id(NEW.category_id)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS cycle_mirror ON "cycle";


CREATE TRIGGER cycle_mirror AFTER INSERT OR UPDATE OR DELETE ON "cycle"
  FOR EACH ROW EXECUTE PROCEDURE cycle_mirror();

----
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO plone;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO plone;
