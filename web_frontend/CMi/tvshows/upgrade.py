from CMi import run_sql

def upgrade_1():
    run_sql('ALTER TABLE tvshows_show ADD COLUMN "auto_erase" bool NOT NULL DEFAULT 1')

def upgrade_2():
    run_sql('ALTER TABLE tvshows_episode ADD COLUMN "watched_count" INTEGER default 0')
    run_sql('UPDATE tvshows_episode SET watched_count = watched')

def upgrade_3():
    run_sql('ALTER TABLE tvshows_show ADD COLUMN "source" VARCHAR(255) NOT NULL DEFAULT ""')

def upgrade_4():
    run_sql('ALTER TABLE tvshows_show ADD COLUMN "ended" bool NOT NULL DEFAULT 0')
