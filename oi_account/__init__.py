from . import models

def pre_init_hook(cr):
    cr.execute("update account_journal set update_posted = true")
