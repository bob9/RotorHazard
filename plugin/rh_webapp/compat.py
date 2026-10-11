'''
The few server facts the web app needs that RHAPI does not offer.

Everything here reads RotorHazard internals (the race context behind RHAPI, the
server module's globals) and is written to survive their absence: each helper
returns a safe default instead of raising, so a change in a future RotorHazard
release hides a feature in the app rather than breaking the plugin. Keep all
such access in this module.
'''
import hmac
import logging
import os
import sys

logger = logging.getLogger(__name__)


def _rc(rhapi):
    return getattr(rhapi, '_racecontext', None)


def _get(obj, *names, default=None):
    '''obj.a.b.c, or the default when any step is missing.'''
    for name in names:
        if obj is None:
            return default
        obj = getattr(obj, name, None)
    return default if obj is None else obj


def _server_module():
    '''The running server module (run as __main__, or imported as 'server' by tests).'''
    for name in ('__main__', 'server'):
        mod = sys.modules.get(name)
        if mod is not None and hasattr(mod, 'RaceContext'):
            return mod
    return None


# --- admin authentication -----------------------------------------------------

def check_auth(rhapi, auth):
    '''True if the request's Basic credentials (or an open timer) give admin access,
    using the server's own check where available.'''
    rc = _rc(rhapi)
    try:
        import AdminAuth  # RotorHazard 4.3+: the check server.py itself uses
        return bool(AdminAuth.check_auth(rc, auth))
    except ImportError:
        pass
    except Exception:
        logger.exception('Admin check failed')
        return False
    # same rules as AdminAuth.check_auth: open when no credentials are set or
    #  the timer has not been set up yet
    user = rhapi.config.get('SECRETS', 'ADMIN_USERNAME') or ''
    password = rhapi.config.get('SECRETS', 'ADMIN_PASSWORD') or ''
    if not user and not password:
        return True
    if first_run(rhapi):
        return True
    if auth is None or auth.username is None or auth.password is None:
        return False
    return hmac.compare_digest(str(auth.username), str(user)) and \
        hmac.compare_digest(str(auth.password), str(password))


def auth_required(rhapi):
    return bool(rhapi.config.get('SECRETS', 'ADMIN_USERNAME') or rhapi.config.get('SECRETS', 'ADMIN_PASSWORD'))


# --- server state --------------------------------------------------------------

def first_run(rhapi):
    '''True until the timer has been set up (no config file yet).'''
    return _get(_rc(rhapi), 'serverconfig', 'config_file_status', default=1) == 0


def set_first_run_done(rhapi):
    serverconfig = _get(_rc(rhapi), 'serverconfig')
    if serverconfig is None or not hasattr(serverconfig, 'config_file_status'):
        return False
    serverconfig.config_file_status = 1
    return True


def restart_required(rhapi):
    return bool(_get(_rc(rhapi), 'serverstate', 'restart_required', default=False))


def server_info(rhapi):
    '''The facts the classic templates get (release, about text...), else RHAPI's.'''
    info = _get(_rc(rhapi), 'serverstate', 'template_info_dict')
    if isinstance(info, dict):
        return info
    try:
        return rhapi.server.info or {}
    except Exception:
        return {}


def num_nodes(rhapi):
    n = _get(_rc(rhapi), 'race', 'num_nodes')
    if isinstance(n, int):
        return n
    try:
        return len(rhapi.interface.seats)
    except Exception:
        return 0


def led_enabled(rhapi):
    '''(LEDs on this timer, LED events either here or on a cluster secondary).'''
    try:
        here = bool(rhapi.led.enabled)
    except Exception:
        here = False
    cluster = _get(_rc(rhapi), 'cluster')
    try:
        secondaries = bool(cluster and cluster.hasRecEventsSecondaries())
    except Exception:
        secondaries = False
    return here, here or secondaries


def vrx_enabled(rhapi):
    try:
        return bool(rhapi.vrxcontrol.enabled)
    except Exception:
        return False


def cluster_has_secondaries(rhapi):
    cluster = _get(_rc(rhapi), 'cluster')
    try:
        return bool(cluster and cluster.hasSecondaries())
    except Exception:
        return False


def node_fw_updatable(rhapi):
    interface = _get(_rc(rhapi), 'interface')
    try:
        return interface is not None and interface.get_fwupd_serial_name() is not None
    except Exception:
        return False


def is_raspberry_pi():
    try:
        import RHUtils
        return bool(RHUtils.is_sys_raspberry_pi())
    except Exception:
        return False


def imdtabler_available():
    '''True/False once the server has checked for IMDTabler (Java), None if unknown.'''
    flag = getattr(_server_module(), 'Use_imdtabler_jar_flag', None)
    return None if flag is None else bool(flag)


def default_node_firmware(rhapi):
    '''The firmware source the classic Update Nodes page starts with.'''
    fn = getattr(_server_module(), 'getDefNodeFwUpdateUrl', None)
    if callable(fn):
        try:
            return fn() or ''
        except Exception:
            logger.exception('Unable to determine the default node firmware')
    configured = rhapi.config.get('GENERAL', 'DEF_NODE_FWUPDATE_URL')
    if configured:
        return configured
    try:
        import stm32loader
        return stm32loader.DEF_BINSRC_STR
    except Exception:
        return ''


# --- plugin panels ---------------------------------------------------------------

def panel_markdowns(rhapi):
    '''[(page, markdown text)] for every Markdown block in a plugin panel.'''
    rhui = _get(_rc(rhapi), 'rhui')
    out = []
    try:
        panels = rhapi.ui.panels
    except Exception:
        panels = _get(rhui, 'ui_panels', default=[])
    for panel in panels or []:
        try:
            for md in rhui.get_panel_markdowns(panel.name):
                out.append((panel.page, str(getattr(md, 'desc', '') or '')))
        except Exception:
            continue
    return out


def core_nav_links(rhapi):
    '''Links registered with rhapi.ui.register_nav_link on servers that have it.'''
    links = _get(_rc(rhapi), 'rhui', 'nav_links', default=[])
    return [dict(l) for l in links if isinstance(l, dict)] if isinstance(links, list) else []


def plugin_removed(plugin):
    '''True if an installed (non-bundled) plugin's folder was deleted since start-up.'''
    if getattr(plugin, 'is_bundled', False):
        return False
    base = getattr(plugin, 'dir', None)
    name = getattr(plugin, 'name', None)
    if not base or not name:
        return False
    return not os.path.isdir(os.path.join(base, 'plugins', name))
