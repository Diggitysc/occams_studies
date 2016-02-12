---
--- avrc_data/specialinstruction -> pirc/specialinstruction
---

DROP FOREIGN TABLE IF EXISTS specialinstruction_ext;


CREATE FOREIGN TABLE specialinstruction_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specialinstruction');


CREATE OR REPLACE FUNCTION specialinstruction_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO specialinstruction_ext (
            id
          , name
          , title
          , description
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , old_db
          , old_id
        )
        VALUES (
            (SELECT val FROM dblink('SELECT nextval(''specialinstruction_id_seq'') AS val') AS sec(val int))
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , (SELECT current_database())
          , NEW.id
        );
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM specialinstruction_ext
        WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE specialinstruction_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS specialinstruction_mirror ON specialinstruction;


CREATE TRIGGER specialinstruction_mirror AFTER INSERT OR UPDATE OR DELETE ON specialinstruction
  FOR EACH ROW EXECUTE PROCEDURE specialinstruction_mirror();