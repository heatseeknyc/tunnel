create table temperatures (
    id serial primary key,
    hub_id text not null,
    cell_id text not null,
    temperature real not null,
    relay boolean not null,
    hub_time timestamp not null,
    time timestamp not null default now(),
    relayed_time timestamp
);
create index on temperatures (hub_id, time desc);
create index on temperatures (cell_id, time desc);

create table hubs (
    id serial primary key,
    hub_id text not null,
    pi_id text not null,
    port integer,
    time timestamp not null default now()
);
create index on hubs (hub_id, time desc);
