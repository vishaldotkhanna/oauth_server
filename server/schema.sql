CREATE TABLE auth_client(
id SERIAL PRIMARY KEY,
name VARCHAR NOT NULL UNIQUE,
oauth_id VARCHAR NOT NULL UNIQUE,
oauth_secret VARCHAR NOT NULL,
status SMALLINT DEFAULT 1,
created_on TIMESTAMP WITH TIME ZONE DEFAULT now(),
last_modified_on TIMESTAMP WITH TIME ZONE DEFAULT now()
) ;

CREATE TABLE auth_user  (
id SERIAL PRIMARY KEY,
oauth_username VARCHAR UNIQUE,
oauth_password VARCHAR,
status SMALLINT DEFAULT 0,
meta_info jsonb DEFAULT '{}',
client_id BIGINT REFERENCES auth_client(id) ON DELETE CASCADE,
created_on timestamp with time zone NOT NULL DEFAULT now(),
last_modified_on timestamp with time zone NOT NULL DEFAULT now()
) ;

INSERT INTO auth_client(name, oauth_id, oauth_secret, status) VALUES('demo_client', 'demo_client', 'admin123', 1) ;
INSERT INTO auth_user(oauth_username, oauth_password, status, meta_info, client_id) VALUES('admin_oauth',
'$pbkdf2-sha256$29000$kDLm/P//fy8l5BxDyHlvjQ$8UXnJmpMpMIEiPRwy6iJ2Td2FQ81pJjClEYLeexZynM', 1,
'{"account_id": "1001"}'::jsonb, (SELECT id FROM auth_client WHERE name = 'demo_client')) ;
