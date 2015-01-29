create table readings (
    hub_id text,
    hub_time timestamp not null,
    cell_id text not null
    temperature real not null,
    time timestamp not null default now()
);

create table hubs (
    id text,
    port integer,
    time timestamp not null default now()
);
