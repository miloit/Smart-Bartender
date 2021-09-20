drop table if exists user;
    create table user (
    uid INTEGER NOT NULL,
    username VARCHAR(100) NOT NULL,
    pass_hash VARCHAR(100) NOT NULL,
    PRIMARY KEY (uid),
    UNIQUE (username)
);
