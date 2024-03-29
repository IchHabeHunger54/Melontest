DROP TABLE IF EXISTS counter;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS tricks;
DROP TABLE IF EXISTS warns;
DROP TABLE IF EXISTS levels;
CREATE TABLE counter (
    id VARCHAR(255) PRIMARY KEY NOT NULL,
    value INT NOT NULL
);
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    channel BIGINT NOT NULL,
    owner BIGINT NOT NULL
);
CREATE TABLE tricks (
    id VARCHAR(255) PRIMARY KEY NOT NULL,
    text VARCHAR(1023) NOT NULL
);
CREATE TABLE warns (
    id SERIAL PRIMARY KEY,
    member BIGINT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    time VARCHAR(255) NOT NULL,
    team_member BIGINT NOT NULL
);
CREATE TABLE levels (
    id BIGINT PRIMARY KEY,
    amount BIGINT
);
