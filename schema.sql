create table temperatures (
    id serial primary key,
    hub_id text not null check (hub_id != ''),
    cell_id text not null check (cell_id != ''),
    temperature real not null,
    sleep_period integer not null,
    relay boolean not null,
    hub_time timestamp not null,
    time timestamp not null default now(),
    relayed_time timestamp
);
create index on temperatures (hub_id, time desc);
create index on temperatures (cell_id, time desc);

create table hubs (
    id serial primary key,
    hub_id text not null check (hub_id != ''),
    pi_id text not null check (pi_id != ''),
    sleep_period integer not null,
    port integer,
    time timestamp not null default now()
);
create index on hubs (hub_id, time desc);

create table xbees (
    id text unique not null,
    short_id text unique not null
);
