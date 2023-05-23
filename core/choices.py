NO_CHANGES = 0
INCLUSION = 1
EXCLUSION = 2
SEVERITY_LEVEL_UPGRADE = 3
SEVERITY_LEVEL_DOWNGRADE = 4
MESSAGE_UPDATE = 5

CHANGE_TYPE = (
    (NO_CHANGES, 'No changes'),
    (INCLUSION, 'Inclusion'),
    (EXCLUSION, 'Exclusion'),
    (SEVERITY_LEVEL_UPGRADE, 'Severity Level Upgrade'),
    (SEVERITY_LEVEL_DOWNGRADE, 'Severity Level Downgrade'),
    (MESSAGE_UPDATE, 'Message update'),
)

GIT_DELETED = 0
GIT_ADDED = 1

GIT_CHANGE_TYPE = (
    (GIT_DELETED, 'Deleted'),
    (GIT_ADDED, 'Added'),
)

GIT_DICT = {
    'added': GIT_ADDED,
    'deleted': GIT_DELETED
}