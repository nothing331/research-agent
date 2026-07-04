create table if not exists sessions (
    id uuid primary key,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    status text not null
);

create table if not exists session_messages (
    id uuid primary key,
    session_id uuid not null references sessions(id),
    role text not null,
    content text not null,
    message_index integer not null,
    created_at timestamptz not null
);

create table if not exists research_runs (
    id uuid primary key,
    session_id uuid not null references sessions(id),
    user_message_id uuid not null references session_messages(id),
    query text not null,
    enhanced_query text not null,
    status text not null,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    completed_at timestamptz
);

create table if not exists tool_calls (
    id uuid primary key,
    research_run_id uuid not null references research_runs(id),
    tool_name text not null,
    status text not null,
    input_payload jsonb not null,
    output_payload jsonb,
    error_message text,
    created_at timestamptz not null,
    completed_at timestamptz
);

create table if not exists reports (
    id uuid primary key,
    research_run_id uuid not null references research_runs(id),
    version integer not null,
    content text not null,
    citations jsonb not null,
    created_at timestamptz not null
);

create table if not exists evaluations (
    id uuid primary key,
    research_run_id uuid not null references research_runs(id),
    report_id uuid not null references reports(id),
    score integer not null,
    feedback jsonb not null,
    created_at timestamptz not null
);
