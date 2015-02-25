create table readings (
    id serial primary key,
    hub_id text,
    hub_time timestamp not null,
    cell_id text not null
    temperature real not null,
    relay boolean not null,
    time timestamp not null default now(),
    relayed_time timestamp
);
create index on readings (hub_id, cell_id, hub_time desc);

create table hubs (
    id text primary key,
    port integer,
    created timestamp not null default now(),
    updated timestamp not null default now()
);

create table hubs_log (
    id serial primary key,
    hub_id text,
    port integer,
    created timestamp not null default now(),
    updated timestamp not null default now()
);
create index on hubs (hub_id, time desc);
