create table if not exists t_url (
 url TEXT NOT NULL PRIMARY KEY,
 regist_date TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP,'localtime')) NOT NULL 
)
