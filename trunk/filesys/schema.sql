--DROP TABLE file CASCADE;
--DROP TABLE directory CASCADE;
--DROP TABLE drive CASCADE;
--DROP TABLE revision CASCADE;
--DROP TABLE file_in_dir CASCADE;
--DROP TABLE image;
--DROP TABLE extra.thumbnail;
--DROP TABLE file_is_image;
--DROP TABLE orphan;

-- May get spurious errors from these few commands, so don't run them in a transaction.
CREATE SCHEMA extra;
CREATE SCHEMA contrib;

CREATE USER localuser PASSWORD 'localuser';

GRANT USAGE ON SCHEMA public, extra, contrib TO localuser;

INSERT INTO pg_db_role_setting
SELECT pg_database.oid, pg_roles.oid, '{"search_path=$user,public,extra,contrib"}'
FROM pg_database, pg_roles
WHERE pg_database.datname = current_database() AND pg_roles.rolname = 'localuser';

CREATE DOMAIN RevisionId AS INTEGER;
CREATE DOMAIN FileId AS INTEGER;
CREATE DOMAIN ImageId AS INTEGER;

CREATE TABLE file
(
    id SERIAL NOT NULL,
    name VARCHAR NOT NULL,
    size BIGINT NOT NULL,
    modified TIMESTAMP,
    md5 CHAR(32),
    
    CONSTRAINT file_pk_id PRIMARY KEY (id),
    
    CONSTRAINT file_ck_md5 CHECK (md5 IS NULL OR length(md5) = 32),
    
    CONSTRAINT file_uq_name_size_modified UNIQUE (name, size, modified)
) WITHOUT OIDS;

CLUSTER file_uq_name_size_modified ON file;

CREATE INDEX file_ix_md5 ON file (md5);
CREATE INDEX file_ix_lower_name ON file (lower(name));


CREATE TABLE directory
(
    id FileId NOT NULL,
    children INTEGER NOT NULL,
    descendants INTEGER NOT NULL,
    
    CONSTRAINT directory_pk_id PRIMARY KEY (id),
    CONSTRAINT directory_fk_id FOREIGN KEY (id) REFERENCES file (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT directory_ck_children_le_descendants CHECK (children <= descendants)
) WITHOUT OIDS;

CLUSTER directory_pk_id ON directory;


CREATE TABLE drive
(
    id FileId NOT NULL,
    free_space BIGINT,
    total_space BIGINT,
    
    CONSTRAINT drive_pk_id PRIMARY KEY (id),
    CONSTRAINT drive_fk_id FOREIGN KEY (id) REFERENCES directory (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT drive_ck_free_space_ge_zero CHECK (free_space >= 0),
    CONSTRAINT drive_ck_total_space_ge_zero CHECK (total_space >= 0)
);

CLUSTER drive_pk_id ON drive;


CREATE TABLE revision
(
    rev_id RevisionId NOT NULL,
    time TIMESTAMP NOT NULL,
    root_id FileId NOT NULL,
    
    CONSTRAINT revision_pk_rev_id PRIMARY KEY (rev_id),
    
    CONSTRAINT revision_fk_root_id FOREIGN KEY (root_id) REFERENCES directory (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) WITHOUT OIDS;

CLUSTER revision_pk_rev_id ON revision;

CREATE INDEX revision_ix_root_id ON revision (root_id);


CREATE TABLE file_in_dir
(
    file_id FileId NOT NULL,
    dir_id FileId NOT NULL,
    
    CONSTRAINT file_in_dir_pk_dir_id_file_id PRIMARY KEY (dir_id, file_id),
    
    CONSTRAINT file_in_dir_fk_dir_id FOREIGN KEY (dir_id) REFERENCES directory (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT file_in_dir_fk_file_id FOREIGN KEY (file_id) REFERENCES file (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT file_in_dir_ck_file_id_lt_dir_id CHECK (file_id < dir_id)
) WITHOUT OIDS;

CLUSTER file_in_dir_pk_dir_id_file_id ON file_in_dir;

CREATE INDEX file_in_dir_ix_file_id ON file_in_dir (file_id);


CREATE TABLE image
(
    id SERIAL NOT NULL,
    
    width INTEGER,
    height INTEGER,
    
    CONSTRAINT image_pk_id PRIMARY KEY (id)
) WITHOUT OIDS;

CLUSTER image_pk_id ON image;


CREATE TABLE image_point
(
    id INTEGER NOT NULL,
    point cube NOT NULL,
    
    CONSTRAINT image_point_pk_id PRIMARY KEY (id),
    
    CONSTRAINT image_point_fk_id FOREIGN KEY (id) REFERENCES image (id)
        ON DELETE CASCADE
    
) WITHOUT OIDS;

CREATE INDEX ON image_point USING GIST (point);


CREATE TABLE extra.thumbnail
(
    id ImageId NOT NULL,
    thumbnail BYTEA,
    
    CONSTRAINT thumbnail_pk_id PRIMARY KEY (id),
    
    CONSTRAINT thumbnail_fk_id FOREIGN KEY (id) REFERENCES image (id)
        ON DELETE CASCADE
) WITHOUT OIDS;


CREATE TABLE file_is_image
(
    file_id FileId NOT NULL,
    image_id ImageId NOT NULL,
    
    CONSTRAINT file_is_image_pk_file_id PRIMARY KEY (file_id),
    
    CONSTRAINT file_is_image_fk_file_id FOREIGN KEY (file_id) REFERENCES file (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT file_is_image_fk_image_id FOREIGN KEY (image_id) REFERENCES image (id)
        ON DELETE CASCADE
) WITHOUT OIDS;

CREATE INDEX file_is_image_ix_image_id ON file_is_image (image_id);

CLUSTER file_is_image_ix_image_id ON file_is_image;


CREATE TABLE image_feature
(
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    weight FLOAT NOT NULL DEFAULT 1.0,
    
    CONSTRAINT image_feature_pk_id PRIMARY KEY (id)

) WITHOUT OIDS;

INSERT INTO image_feature VALUES (1, 'ravg', 1.0);
INSERT INTO image_feature VALUES (2, 'gavg', 1.0);
INSERT INTO image_feature VALUES (3, 'bavg', 1.0);
INSERT INTO image_feature VALUES (4, 'savg', 1.0);
INSERT INTO image_feature VALUES (5, 'lavg', 1.0);
INSERT INTO image_feature VALUES (6, 'rsd', 1.0);
INSERT INTO image_feature VALUES (7, 'gsd', 1.0);
INSERT INTO image_feature VALUES (8, 'bsd', 1.0);
INSERT INTO image_feature VALUES (9, 'ssd', 1.0);
INSERT INTO image_feature VALUES (10, 'lsd', 1.0);
INSERT INTO image_feature VALUES (11, 'rlavg', 1.0);
INSERT INTO image_feature VALUES (12, 'glavg', 1.0);
INSERT INTO image_feature VALUES (13, 'blavg', 1.0);


CREATE TABLE orphan
(
    id FileId,
    CONSTRAINT orphan_pk_id PRIMARY KEY (id),
    CONSTRAINT orphan_fk_id FOREIGN KEY (id) REFERENCES file (id) ON DELETE CASCADE
) WITHOUT OIDS;

CLUSTER orphan_pk_id ON orphan;


CREATE TABLE deleted
(
    id FileId,
    duplicate_of FileId,
    
    CONSTRAINT deleted_pk_id PRIMARY KEY (id),
    
    CONSTRAINT deleted_fk_id FOREIGN KEY (id) REFERENCES file (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT deleted_fk_duplicate_of FOREIGN KEY (duplicate_of) REFERENCES file (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) WITHOUT OIDS;

CLUSTER deleted_pk_id ON deleted;

CREATE INDEX deleted_ix_duplicate_of ON deleted (duplicate_of);


CREATE TABLE config
(
    commit_interval INTEGER DEFAULT 60,
    commit_interval_max INTEGER DEFAULT 300,
    
    thumbnail_height INTEGER DEFAULT 100,
    thumbnail_width INTEGER DEFAULT 100,
    thumbnail_type TEXT DEFAULT 'image/png',
    
    ignore_regex TEXT DEFAULT '^$',
    ignore_regex_i TEXT DEFAULT '^$',
    
    no_md5_regex TEXT DEFAULT '/pagefile.sys$'
);

INSERT INTO config DEFAULT VALUES;


GRANT SELECT,INSERT,UPDATE,DELETE ON
    file, directory, drive, revision, file_in_dir,
    image, image_point, image_feature, extra.thumbnail, file_is_image,
    deleted, config
TO localuser;

GRANT SELECT,UPDATE ON
    file_id_seq, image_id_seq
TO localuser;


CREATE TYPE rev_path AS (rev_id int4, path text);

CREATE TYPE name_size_modified AS (name TEXT, size BIGINT, modified TIMESTAMP);
