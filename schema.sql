create table readings (
    id serial primary key,
    hub_id text not null,
    hub_time timestamp not null,
    cell_id text not null
    temperature real not null,
    relay boolean not null,
    time timestamp not null default now(),
    relayed_time timestamp
);
create index on readings (hub_id, hub_time desc);
create index on readings (cell_id, hub_time desc);

create table hubs (
    id text primary key,
    xbee_id text,
    port integer,
    time timestamp not null default now()
);
create index on hubs (xbee_id);

create table hubs_log (
    id serial primary key,
    hub_id text not null,
    xbee_id text,
    port integer,
    time timestamp not null default now()
);
create index on hubs_log (hub_id, time desc);
